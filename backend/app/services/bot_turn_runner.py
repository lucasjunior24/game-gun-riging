from app.dtos.character import IdentityDTO
from app.engine import GameEngine
from app.engine.dice import MAX_ROLLS, DiceFace
from app.engine.rules import RESOLUTION_ORDER, Assignment
from app.engine.seating import valid_targets
from app.engine.state import EngineState, GameStatus, TurnPhase
from app.services.policy_service import ShotPolicyService


class BotTurnRunner:
    """Bot provisorio que joga um turno completo pelas regras do motor."""

    def __init__(self, engine: GameEngine, policy: ShotPolicyService):
        self.engine = engine
        self.policy = policy

    def play_turn(self, state: EngineState) -> EngineState:
        seat = state.turn.seat
        state = self._play_rolling(state, seat)
        if not self._still_resolving(state, seat):
            return state
        return self.resolve_pending(state, seat)

    def _play_rolling(self, state: EngineState, seat: int) -> EngineState:
        self.engine.roll(state, seat)
        while self._still_rolling(state, seat) and state.turn.rolls_used < MAX_ROLLS:
            reroll = self._choose_rerolls(state, seat)
            if not reroll:
                self.engine.stop_rolling(state, seat)
                break
            self.engine.roll(state, seat, reroll)
        return state

    def resolve_pending(self, state: EngineState, seat: int) -> EngineState:
        """Resolve os dados pendentes um a um, escolhendo o alvo depois de cada aplicacao.

        Isso evita que uma morte no meio da resolucao deixe um alvo escolhido antes invalido.
        """
        while self._still_resolving(state, seat) and self.engine.pending_dice(state):
            assignment = self._choose_next_assignment(state, seat)
            state = self.engine.resolve_one(state, seat, assignment)

        if self._still_resolving(state, seat):
            state = self.engine.resolve(state, seat, [])
        return state

    def _choose_rerolls(self, state: EngineState, seat: int) -> set[int]:
        me = state.players[seat]
        reroll = set()
        for die in state.turn.dice:
            if not die.can_reroll:
                continue
            if die.face is DiceFace.ARROW:
                reroll.add(die.index)
            elif die.face is DiceFace.BEER and me.life == me.max_life:
                reroll.add(die.index)
        return reroll

    def _choose_next_assignment(self, state: EngineState, seat: int) -> Assignment:
        pending = self.engine.pending_dice(state)
        index = min(pending, key=lambda i: (RESOLUTION_ORDER[state.turn.dice[i].face], i))
        face = state.turn.dice[index].face
        candidates = valid_targets(state, seat, face)
        if face is DiceFace.BEER:
            target = self._choose_beer_target(state, seat, candidates)
        else:
            target = self.policy.rank_targets(state, seat, candidates)[0]
        return Assignment(dice_index=index, target_seat=target)

    def _choose_beer_target(self, state: EngineState, seat: int, candidates: list[int]) -> int:
        me = state.players[seat]
        if me.identity in (IdentityDTO.ASSISTENTE, IdentityDTO.RENEGADO):
            sheriff = next((p for p in state.players if p.identity is IdentityDTO.XERIFE), None)
            if sheriff and sheriff.seat in candidates and sheriff.life < sheriff.max_life and me.life > 2:
                return sheriff.seat
        return seat

    def _still_rolling(self, state: EngineState, seat: int) -> bool:
        return (
            state.status is GameStatus.RUNNING
            and state.turn.seat == seat
            and state.turn.phase is TurnPhase.ROLLING
        )

    def _still_resolving(self, state: EngineState, seat: int) -> bool:
        return (
            state.status is GameStatus.RUNNING
            and state.turn.seat == seat
            and state.turn.phase is TurnPhase.RESOLVING
        )
