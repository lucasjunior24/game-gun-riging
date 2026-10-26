"""Helpers dos testes do bot. Nome proprio para nao colidir com os outros conftest.py."""

import random

from app.dtos.character import IdentityDTO
from app.engine.dice import DiceFace
from app.engine.events import EventType, GameEvent
from app.engine.rules import GameEngine, PlayerSpec
from app.engine.state import EngineState, TurnPhase

XERIFE = IdentityDTO.XERIFE
ASSISTENTE = IdentityDTO.ASSISTENTE
FORA_DA_LEI = IdentityDTO.FORA_DA_LEI
RENEGADO = IdentityDTO.RENEGADO

# Sem embaralhar, os papeis seguem ROLE_DISTRIBUTION:
#   5 jogadores: 0 Xerife, 1 Renegado, 2 FL, 3 FL, 4 Assistente
#   7 jogadores: ... 5 FL, 6 Assistente; 8 jogadores: ... 7 Renegado


def new_state(total: int, life: int = 8, seed: int = 0) -> EngineState:
    specs = [
        PlayerSpec(user_id=i + 1, user_name=f"P{i}", is_bot=True, character="Teste", life=life)
        for i in range(total)
    ]
    return GameEngine().new_game("g", specs, random.Random(seed), shuffle_roles=False)


def add_event(
    state: EngineState,
    event_type: EventType,
    actor: int,
    target: int,
    options: list[int],
) -> None:
    """Registra uma escolha publica de alvo, como o motor faria."""
    state.events.append(
        GameEvent(
            id=state.next_event_id,
            type=event_type,
            round_number=state.round_number,
            turn_number=state.turn_number,
            actor_seat=actor,
            target_seat=target,
            actor_public_identity=state.players[actor].public_identity,
            target_public_identity=state.players[target].public_identity,
            data={"valid_target_seats": options},
        )
    )
    state.next_event_id += 1


def kill(state: EngineState, seat: int) -> None:
    state.players[seat].life = 0
    state.players[seat].revealed = True


def set_turn(
    state: EngineState,
    seat: int,
    faces: list[DiceFace],
    phase: TurnPhase = TurnPhase.RESOLVING,
    rolls_used: int = 1,
) -> None:
    state.turn.seat = seat
    state.turn.phase = phase
    state.turn.rolls_used = rolls_used
    for die, face in zip(state.turn.dice, faces):
        die.face = face
        die.locked = face is DiceFace.DYNAMITE
        die.resolved = False
