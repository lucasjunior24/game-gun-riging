import pytest

from app.engine.dice import DiceFace
from app.engine.errors import RuleViolation
from app.engine.rules import GameEngine
from app.engine.state import TurnPhase

from conftest import ScriptedRng, make_specs

SHOT_1 = DiceFace.SHOT_1
SHOT_2 = DiceFace.SHOT_2
DYNAMITE = DiceFace.DYNAMITE
BEER = DiceFace.BEER
ARROW = DiceFace.ARROW
GATLING = DiceFace.GATLING


def new_game(faces, total=5):
    engine = GameEngine()
    rng = ScriptedRng(faces)
    state = engine.new_game("g", make_specs(total), rng, shuffle_roles=False)
    return engine, state


def test_first_roll_rolls_all_five_dice():
    engine, state = new_game([SHOT_1, SHOT_2, BEER, GATLING, ARROW, ARROW])
    engine.roll(state, state.turn.seat)
    faces = [die.face for die in state.turn.dice]
    assert faces == [SHOT_1, SHOT_2, BEER, GATLING, ARROW]
    assert state.turn.rolls_used == 1
    assert state.turn.phase is TurnPhase.ROLLING


def test_reroll_requires_at_least_one_index():
    engine, state = new_game([SHOT_1, SHOT_2, BEER, GATLING, ARROW, ARROW])
    seat = state.turn.seat
    engine.roll(state, seat)
    with pytest.raises(RuleViolation):
        engine.roll(state, seat, set())


def test_dynamite_locks_and_cannot_be_rerolled():
    engine, state = new_game([SHOT_1, SHOT_2, DYNAMITE, GATLING, ARROW, SHOT_1])
    seat = state.turn.seat
    engine.roll(state, seat)
    assert state.turn.dice[2].locked is True
    with pytest.raises(RuleViolation):
        engine.roll(state, seat, {2})


def test_third_dynamite_damages_roller_and_ends_rolling():
    engine, state = new_game(
        [DYNAMITE, DYNAMITE, DYNAMITE, SHOT_1, BEER]
    )
    seat = state.turn.seat
    sheriff = state.players[seat]
    max_life = sheriff.max_life
    engine.roll(state, seat)
    assert sheriff.life == max_life - 1
    assert state.turn.phase is TurnPhase.RESOLVING


def test_rolls_are_limited_to_three():
    engine, state = new_game(
        [SHOT_1, SHOT_1, SHOT_1, SHOT_1, SHOT_1]
        + [SHOT_2, SHOT_2, SHOT_2, SHOT_2, SHOT_2]
        + [BEER, BEER, BEER, BEER, BEER]
    )
    seat = state.turn.seat
    engine.roll(state, seat)
    engine.roll(state, seat, {0, 1, 2, 3, 4})
    engine.roll(state, seat, {0, 1, 2, 3, 4})
    assert state.turn.rolls_used == 3
    assert state.turn.phase is TurnPhase.RESOLVING
    with pytest.raises(RuleViolation):
        engine.roll(state, seat, {0})


def test_stop_rolling_requires_at_least_one_roll():
    engine, state = new_game([SHOT_1, SHOT_2, BEER, GATLING, ARROW])
    with pytest.raises(RuleViolation):
        engine.stop_rolling(state, state.turn.seat)


def test_stop_rolling_moves_to_resolving_phase():
    engine, state = new_game([SHOT_1, SHOT_2, BEER, GATLING, ARROW])
    seat = state.turn.seat
    engine.roll(state, seat)
    engine.stop_rolling(state, seat)
    assert state.turn.phase is TurnPhase.RESOLVING


def test_only_current_player_can_roll():
    engine, state = new_game([SHOT_1, SHOT_2, BEER, GATLING, ARROW])
    other_seat = (state.turn.seat + 1) % len(state.players)
    with pytest.raises(RuleViolation):
        engine.roll(state, other_seat)
