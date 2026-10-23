import random

from app.dtos.character import IdentityDTO, TeamDTO
from app.engine.dice import DiceFace
from app.engine.rules import Assignment, GameEngine
from app.engine.state import GameStatus, TurnPhase

from conftest import make_specs

SHOT_1 = DiceFace.SHOT_1
FILLER = DiceFace.ARROW


def resolving_state(total, life=1):
    engine = GameEngine()
    state = engine.new_game("g", make_specs(total, life=life), random.Random(0), shuffle_roles=False)
    return engine, state


def kill_with_shot_1(engine, state, shooter_seat, target_seat):
    for die in state.turn.dice:
        die.face = FILLER
    state.turn.dice[0].face = SHOT_1
    state.turn.rolls_used = 1
    state.turn.phase = TurnPhase.RESOLVING
    state.turn.seat = shooter_seat
    return engine.resolve(state, shooter_seat, [Assignment(dice_index=0, target_seat=target_seat)])


def seat_of(state, identity: IdentityDTO) -> int:
    return next(p.seat for p in state.players if p.identity is identity)


def test_outlaws_win_when_sheriff_dies_and_renegade_is_not_alone():
    engine, state = resolving_state(total=5)
    sheriff_seat = seat_of(state, IdentityDTO.XERIFE)
    renegade_seat = seat_of(state, IdentityDTO.RENEGADO)
    state.players[sheriff_seat].life = 1  # desconta o bonus de +2 do Xerife para o teste
    # O renegado esta ao lado do Xerife; mata-lo deixa foras da lei e assistente vivos tambem.
    result = kill_with_shot_1(engine, state, renegade_seat, sheriff_seat)

    assert result.status is GameStatus.DONE
    assert result.winner is TeamDTO.FORA_DA_LEI


def test_renegade_wins_when_the_only_other_survivor():
    engine, state = resolving_state(total=4, life=1)
    sheriff_seat = seat_of(state, IdentityDTO.XERIFE)
    renegade_seat = seat_of(state, IdentityDTO.RENEGADO)
    outlaw_seats = [p.seat for p in state.players if p.identity is IdentityDTO.FORA_DA_LEI]

    for outlaw_seat in outlaw_seats:
        state.players[outlaw_seat].life = 0
    state.players[sheriff_seat].life = 1  # desconta o bonus de +2 do Xerife para o teste

    result = kill_with_shot_1(engine, state, renegade_seat, sheriff_seat)

    assert result.status is GameStatus.DONE
    assert result.winner is TeamDTO.RENEGADO


def test_sheriff_team_wins_when_no_enemies_remain():
    engine, state = resolving_state(total=5, life=1)
    sheriff_seat = seat_of(state, IdentityDTO.XERIFE)
    renegade_seat = seat_of(state, IdentityDTO.RENEGADO)
    outlaw_seats = [p.seat for p in state.players if p.identity is IdentityDTO.FORA_DA_LEI]

    for outlaw_seat in outlaw_seats:
        state.players[outlaw_seat].life = 0

    result = kill_with_shot_1(engine, state, sheriff_seat, renegade_seat)

    assert result.status is GameStatus.DONE
    assert result.winner is TeamDTO.XERIFE
