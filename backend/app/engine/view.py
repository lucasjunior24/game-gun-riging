from dataclasses import dataclass, field

from app.dtos.character import IdentityDTO
from app.engine.dice import DiceFace
from app.engine.events import GameEvent
from app.engine.seating import distance
from app.engine.state import EngineState, GameStatus, TurnPhase


@dataclass(frozen=True)
class PlayerSnapshot:
    seat: int
    user_id: int
    user_name: str
    life: int
    max_life: int
    arrows: int
    is_alive: bool
    is_bot: bool
    public_identity: IdentityDTO | None
    distance_from_viewer: int | None


@dataclass(frozen=True)
class DieSnapshot:
    index: int
    face: DiceFace | None
    locked: bool
    resolved: bool


@dataclass(frozen=True)
class PlayerObservation:
    """Tudo que um jogador pode saber. Nada aqui revela papel oculto de outro."""

    viewer_seat: int
    my_identity: IdentityDTO
    players: tuple[PlayerSnapshot, ...]
    current_seat: int
    phase: TurnPhase
    rolls_used: int
    dice: tuple[DieSnapshot, ...]
    arrows_in_pile: int
    round_number: int
    turn_number: int
    status: GameStatus
    events: tuple[GameEvent, ...] = field(default_factory=tuple)


def build_observation(state: EngineState, viewer_seat: int) -> PlayerObservation:
    viewer = state.players[viewer_seat]
    players = tuple(
        PlayerSnapshot(
            seat=p.seat,
            user_id=p.user_id,
            user_name=p.user_name,
            life=p.life,
            max_life=p.max_life,
            arrows=p.arrows,
            is_alive=p.is_alive,
            is_bot=p.is_bot,
            public_identity=p.public_identity,
            distance_from_viewer=(
                distance(state, viewer_seat, p.seat)
                if p.is_alive and viewer.is_alive
                else None
            ),
        )
        for p in state.players
    )
    return PlayerObservation(
        viewer_seat=viewer_seat,
        my_identity=viewer.identity,
        players=players,
        current_seat=state.turn.seat,
        phase=state.turn.phase,
        rolls_used=state.turn.rolls_used,
        dice=tuple(DieSnapshot(d.index, d.face, d.locked, d.resolved) for d in state.turn.dice),
        arrows_in_pile=state.arrows_in_pile,
        round_number=state.round_number,
        turn_number=state.turn_number,
        status=state.status,
        events=tuple(state.events),  # eventos ja guardam so identidades publicas (Fase 1)
    )
