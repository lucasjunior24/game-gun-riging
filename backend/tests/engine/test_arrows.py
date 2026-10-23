from app.dtos.character import IdentityDTO
from app.engine.dice import DiceFace
from app.engine.rules import GameEngine
from app.engine.state import ARROWS_TOTAL, TurnPhase

from conftest import ScriptedRng, make_specs

ARROW = DiceFace.ARROW
SHOT_1 = DiceFace.SHOT_1
BEER = DiceFace.BEER
GATLING = DiceFace.GATLING


def new_game(faces, total=5, life=4):
    engine = GameEngine()
    rng = ScriptedRng(faces)
    state = engine.new_game("g", make_specs(total, life=life), rng, shuffle_roles=False)
    return engine, state


def test_arrow_rolled_is_taken_and_leaves_the_pile():
    engine, state = new_game([ARROW, SHOT_1, SHOT_1, SHOT_1, SHOT_1])
    seat = state.turn.seat
    engine.roll(state, seat)
    assert state.players[seat].arrows == 1
    assert state.arrows_in_pile == ARROWS_TOTAL - 1


def test_indian_attack_triggers_when_pile_runs_out():
    engine, state = new_game([ARROW, SHOT_1, SHOT_1, SHOT_1, SHOT_1], total=5, life=4)
    seat = state.turn.seat
    other_seats = [p.seat for p in state.players if p.seat != seat]
    state.arrows_in_pile = 1
    state.players[other_seats[0]].arrows = 2
    before_life = state.players[other_seats[0]].life

    engine.roll(state, seat)

    assert state.arrows_in_pile == ARROWS_TOTAL
    assert state.players[other_seats[0]].life == before_life - 2
    for player in state.players:
        assert player.arrows == 0


def test_dead_player_does_not_take_damage_from_indian_attack():
    engine, state = new_game([ARROW, SHOT_1, SHOT_1, SHOT_1, SHOT_1], total=4, life=4)
    seat = state.turn.seat
    other = (seat + 1) % 4
    state.players[other].life = 0
    state.players[other].arrows = 3

    state.arrows_in_pile = 1

    engine.roll(state, seat)

    assert state.players[other].life == 0


def test_turn_ends_early_if_indian_attack_kills_the_current_roller():
    engine, state = new_game([ARROW], total=4, life=1)
    # Usa um jogador comum (nao o Xerife) para nao ganhar o bonus de +2 de vida.
    seat = next(p.seat for p in state.players if p.identity is not IdentityDTO.XERIFE)
    state.turn.seat = seat
    state.players[seat].arrows = 1
    state.arrows_in_pile = 1

    engine.roll(state, seat)

    assert state.players[seat].is_alive is False
    assert state.turn.seat != seat
    assert state.turn.phase is TurnPhase.ROLLING
