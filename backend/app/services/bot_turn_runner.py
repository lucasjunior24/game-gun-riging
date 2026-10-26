from dataclasses import replace

from app.bot.agent import Agent, Decision
from app.engine import GameEngine
from app.engine.dice import MAX_ROLLS
from app.engine.events import EventType
from app.engine.state import EngineState, GameStatus, TurnPhase
from app.engine.view import build_observation


class BotTurnRunner:
    """Joga um turno completo de bot pedindo cada decisao ao agente.

    O agente so recebe a observacao do bot, nunca o estado real.
    """

    def __init__(self, engine: GameEngine, agent: Agent):
        self.engine = engine
        self.agent = agent

    def play_turn(self, state: EngineState) -> EngineState:
        seat = state.turn.seat
        state = self._play_rolling(state, seat)
        if not self._still_resolving(state, seat):
            return state
        return self.resolve_pending(state, seat)

    def _play_rolling(self, state: EngineState, seat: int) -> EngineState:
        self.engine.roll(state, seat)
        while self._still_rolling(state, seat) and state.turn.rolls_used < MAX_ROLLS:
            decision = self.agent.choose_reroll(build_observation(state, seat))
            if not decision.action:
                self.engine.stop_rolling(state, seat)
                break
            since = state.next_event_id
            self.engine.roll(state, seat, decision.action)
            self._annotate(state, since, seat, decision, (EventType.DICE_ROLLED,))
        return state

    def resolve_pending(self, state: EngineState, seat: int) -> EngineState:
        """Aplica o plano do agente dado a dado. Se alguem morre, pede um plano novo.

        A morte muda distancias (um alvo escolhido antes pode ficar invalido) e revela
        um papel, o que muda a crenca do agente.
        """
        while self._still_resolving(state, seat) and self.engine.pending_dice(state):
            decision = self.agent.choose_assignments(build_observation(state, seat))
            since = state.next_event_id
            alive = len(state.alive_players())
            for assignment in decision.action:
                state = self.engine.resolve_one(state, seat, assignment)
                if not self._still_resolving(state, seat) or len(state.alive_players()) < alive:
                    break
            self._annotate(state, since, seat, decision, (EventType.SHOT, EventType.BEER))

        if self._still_resolving(state, seat):
            state = self.engine.resolve(state, seat, [])
        return state

    def _annotate(
        self,
        state: EngineState,
        since: int,
        seat: int,
        decision: Decision,
        types: tuple[EventType, ...],
    ) -> None:
        """Grava o motivo e a confianca da decisao nos eventos que ela gerou."""
        for i, event in enumerate(state.events):
            if event.id >= since and event.actor_seat == seat and event.type in types:
                # Troca o evento em vez de alterar: eventos sao compartilhados entre copias do estado
                state.events[i] = replace(
                    event,
                    data={
                        **event.data,
                        "reason": decision.reason,
                        "confidence": round(decision.confidence, 3),
                    },
                )

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
