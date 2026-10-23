import random
from dataclasses import dataclass

from app.dtos.character import IdentityDTO, TeamDTO
from app.engine.dice import DYNAMITE_LIMIT, FACES, GATLING_MIN, MAX_ROLLS, DiceFace
from app.engine.errors import RuleViolation
from app.engine.events import EventType, GameEvent
from app.engine.roles import deal_roles
from app.engine.seating import valid_targets
from app.engine.state import (
    ARROWS_TOTAL,
    EnginePlayer,
    EngineState,
    GameStatus,
    TurnPhase,
    TurnState,
)

TARGETED_FACES = (DiceFace.SHOT_1, DiceFace.SHOT_2, DiceFace.BEER)
RESOLUTION_ORDER = {DiceFace.SHOT_1: 0, DiceFace.SHOT_2: 1, DiceFace.BEER: 2}


@dataclass
class PlayerSpec:
    user_id: int
    user_name: str
    is_bot: bool
    character: str
    life: int
    power: str = ""


@dataclass
class Assignment:
    dice_index: int
    target_seat: int


class GameEngine:
    # ---------- setup ----------

    def new_game(
        self,
        game_id: str,
        specs: list[PlayerSpec],
        rng: random.Random,
        shuffle_roles: bool = True,
    ) -> EngineState:
        roles = deal_roles(len(specs), rng, shuffle_roles)
        players = []
        for seat, (spec, identity) in enumerate(zip(specs, roles)):
            bonus = 2 if identity is IdentityDTO.XERIFE else 0
            players.append(
                EnginePlayer(
                    seat=seat,
                    user_id=spec.user_id,
                    user_name=spec.user_name,
                    identity=identity,
                    max_life=spec.life + bonus,
                    life=spec.life + bonus,
                    is_bot=spec.is_bot,
                    character=spec.character,
                    power=spec.power,
                )
            )
        sheriff_seat = next(p.seat for p in players if p.identity is IdentityDTO.XERIFE)
        state = EngineState(
            game_id=game_id, players=players, rng=rng, turn=TurnState(seat=sheriff_seat)
        )
        self._emit(state, EventType.TURN_STARTED, actor_seat=sheriff_seat)
        return state

    # ---------- rolagem ----------

    def roll(self, state: EngineState, seat: int, reroll_indexes: set[int] | None = None) -> None:
        turn = self._require_phase(state, seat, TurnPhase.ROLLING)
        if turn.rolls_used >= MAX_ROLLS:
            raise RuleViolation("Sem rolagens restantes")

        if turn.rolls_used == 0:
            indexes = {die.index for die in turn.dice}
        else:
            indexes = set(reroll_indexes or ())
            if not indexes:
                raise RuleViolation("Escolha ao menos um dado para rolar de novo")
            for index in indexes:
                if not turn.dice[index].can_reroll:
                    raise RuleViolation("Dinamite nao pode ser rolada de novo")

        for index in sorted(indexes):
            die = turn.dice[index]
            die.face = state.rng.choice(FACES)
            die.locked = die.face is DiceFace.DYNAMITE
            die.resolved = False
            self._emit(
                state,
                EventType.DICE_ROLLED,
                actor_seat=seat,
                data={"index": index, "face": die.face.value},
            )
            if die.face is DiceFace.ARROW:
                self._take_arrow(state, seat)
                if self._turn_interrupted(state, seat):
                    return

        turn.rolls_used += 1

        dynamites = sum(1 for die in turn.dice if die.face is DiceFace.DYNAMITE)
        if dynamites >= DYNAMITE_LIMIT:
            self._emit(state, EventType.DYNAMITE_EXPLODED, actor_seat=seat)
            self._damage(state, seat, seat, 1)
            if self._turn_interrupted(state, seat):
                return
            turn.phase = TurnPhase.RESOLVING
        elif turn.rolls_used == MAX_ROLLS:
            turn.phase = TurnPhase.RESOLVING

    def stop_rolling(self, state: EngineState, seat: int) -> None:
        turn = self._require_phase(state, seat, TurnPhase.ROLLING)
        if turn.rolls_used == 0:
            raise RuleViolation("Role os dados ao menos uma vez")
        turn.phase = TurnPhase.RESOLVING

    # ---------- resolucao ----------

    def pending_dice(self, state: EngineState) -> list[int]:
        return [
            die.index
            for die in state.turn.dice
            if die.face in TARGETED_FACES and not die.resolved
        ]

    def resolve_one(self, state: EngineState, seat: int, assignment: Assignment) -> EngineState:
        """Aplica um unico dado numa copia do estado e devolve o novo estado."""
        self._require_phase(state, seat, TurnPhase.RESOLVING)
        draft = state.clone()

        pending = self.pending_dice(draft)
        if assignment.dice_index not in pending:
            raise RuleViolation(f"Dado {assignment.dice_index} nao esta pendente")

        face = draft.turn.dice[assignment.dice_index].face
        next_order = min(RESOLUTION_ORDER[draft.turn.dice[index].face] for index in pending)
        if RESOLUTION_ORDER[face] != next_order:
            raise RuleViolation("Resolva os dados na ordem 1, 2 e Cerveja")

        if assignment.target_seat not in valid_targets(draft, seat, face):
            raise RuleViolation(f"Alvo invalido para o dado {assignment.dice_index}")

        draft.turn.dice[assignment.dice_index].resolved = True
        if face is DiceFace.BEER:
            self._heal(draft, seat, assignment.target_seat)
        else:
            self._emit(
                draft,
                EventType.SHOT,
                actor_seat=seat,
                target_seat=assignment.target_seat,
                amount=1,
            )
            self._damage(draft, seat, assignment.target_seat, 1)

        if draft.status is GameStatus.DONE or not draft.players[seat].is_alive:
            return draft

        if not self.pending_dice(draft):
            self._finish_resolution(draft, seat)
        return draft

    def resolve(self, state: EngineState, seat: int, assignments: list[Assignment]) -> EngineState:
        """Aplica todos os dados pendentes numa copia do estado e devolve o novo estado.

        Se algo for invalido, levanta RuleViolation e o estado original fica intacto.
        """
        self._require_phase(state, seat, TurnPhase.RESOLVING)
        pending = self.pending_dice(state)

        by_index = {a.dice_index: a for a in assignments}
        if sorted(by_index) != sorted(pending) or len(by_index) != len(assignments):
            raise RuleViolation("Cada dado de 1, 2 e Cerveja precisa de exatamente um alvo")

        ordered = sorted(
            assignments,
            key=lambda a: (RESOLUTION_ORDER[state.turn.dice[a.dice_index].face], a.dice_index),
        )

        result = state
        for assignment in ordered:
            if result.status is GameStatus.DONE or not result.players[seat].is_alive:
                return result
            result = self.resolve_one(result, seat, assignment)

        if (
            result.status is GameStatus.RUNNING
            and result.turn.seat == seat
            and result.turn.phase is TurnPhase.RESOLVING
        ):
            self._finish_resolution(result, seat)
        return result

    def _finish_resolution(self, state: EngineState, seat: int) -> None:
        gatlings = sum(1 for die in state.turn.dice if die.face is DiceFace.GATLING)
        if gatlings >= GATLING_MIN:
            self._gatling(state, seat)
            if state.status is GameStatus.DONE:
                return
        self._next_turn(state)

    # ---------- efeitos ----------

    def _take_arrow(self, state: EngineState, seat: int) -> None:
        state.players[seat].arrows += 1
        state.arrows_in_pile -= 1
        self._emit(state, EventType.ARROW_TAKEN, actor_seat=seat)
        if state.arrows_in_pile == 0:
            self._indian_attack(state)

    def _indian_attack(self, state: EngineState) -> None:
        self._emit(state, EventType.INDIAN_ATTACK)
        for player in state.alive_players():
            if player.arrows:
                self._damage(state, None, player.seat, player.arrows)
        for player in state.players:
            player.arrows = 0
        state.arrows_in_pile = ARROWS_TOTAL

    def _gatling(self, state: EngineState, seat: int) -> None:
        self._emit(state, EventType.GATLING, actor_seat=seat)
        shooter = state.players[seat]
        state.arrows_in_pile += shooter.arrows
        shooter.arrows = 0
        for player in state.alive_players():
            if player.seat != seat:
                self._damage(state, seat, player.seat, 1)

    def _heal(self, state: EngineState, seat: int, target_seat: int) -> None:
        target = state.players[target_seat]
        healed = min(1, target.max_life - target.life)
        target.life += healed
        self._emit(state, EventType.BEER, actor_seat=seat, target_seat=target_seat, amount=healed)

    def _damage(self, state: EngineState, source_seat: int | None, target_seat: int, amount: int) -> None:
        target = state.players[target_seat]
        if not target.is_alive:
            return
        target.life = max(0, target.life - amount)
        self._emit(state, EventType.DAMAGE, actor_seat=source_seat, target_seat=target_seat, amount=amount)
        if not target.is_alive:
            self._kill(state, target)

    def _kill(self, state: EngineState, player: EnginePlayer) -> None:
        player.revealed = True
        state.arrows_in_pile += player.arrows
        player.arrows = 0
        self._emit(state, EventType.DEATH, target_seat=player.seat)
        self._check_winner(state)

    # ---------- vitoria e turnos ----------

    def _check_winner(self, state: EngineState) -> None:
        if state.status is GameStatus.DONE:
            return
        alive = state.alive_players()
        sheriff_alive = any(p.identity is IdentityDTO.XERIFE for p in alive)
        enemies_alive = any(
            p.identity in (IdentityDTO.FORA_DA_LEI, IdentityDTO.RENEGADO) for p in alive
        )

        if not sheriff_alive:
            only_renegade = len(alive) == 1 and alive[0].identity is IdentityDTO.RENEGADO
            state.winner = TeamDTO.RENEGADO if only_renegade else TeamDTO.FORA_DA_LEI
        elif not enemies_alive:
            state.winner = TeamDTO.XERIFE
        else:
            return
        state.status = GameStatus.DONE
        self._emit(state, EventType.VICTORY, data={"winner": state.winner.value})

    def _turn_interrupted(self, state: EngineState, seat: int) -> bool:
        if state.status is GameStatus.DONE:
            return True
        if not state.players[seat].is_alive:
            self._next_turn(state)
            return True
        return False

    def _next_turn(self, state: EngineState) -> None:
        current = state.turn.seat
        total = len(state.players)
        seat = current
        for step in range(1, total + 1):
            seat = (current + step) % total
            if state.players[seat].is_alive:
                break
        if seat <= current:
            state.round_number += 1
        state.turn_number += 1
        state.turn = TurnState(seat=seat)
        self._emit(state, EventType.TURN_STARTED, actor_seat=seat)

    # ---------- utilidades ----------

    def _require_phase(self, state: EngineState, seat: int, phase: TurnPhase) -> TurnState:
        if state.status is GameStatus.DONE:
            raise RuleViolation("A partida ja terminou")
        if state.turn.seat != seat:
            raise RuleViolation("Nao e a vez deste jogador")
        if state.turn.phase is not phase:
            raise RuleViolation(f"Acao nao permitida na fase {state.turn.phase.value}")
        return state.turn

    def _emit(
        self,
        state: EngineState,
        event_type: EventType,
        actor_seat: int | None = None,
        target_seat: int | None = None,
        amount: int = 0,
        data: dict | None = None,
    ) -> None:
        actor = state.players[actor_seat] if actor_seat is not None else None
        target = state.players[target_seat] if target_seat is not None else None
        state.events.append(
            GameEvent(
                type=event_type,
                round_number=state.round_number,
                turn_number=state.turn_number,
                actor_seat=actor_seat,
                target_seat=target_seat,
                amount=amount,
                actor_public_identity=actor.public_identity if actor else None,
                target_public_identity=target.public_identity if target else None,
                data=data or {},
            )
        )
