from app.dtos.character import IdentityDTO
from app.engine.dice import DiceFace
from app.engine.rules import GameEngine
from app.engine.seating import distance, valid_targets

from conftest import make_specs


def new_state(total: int):
    engine = GameEngine()
    import random

    state = engine.new_game("g", make_specs(total), random.Random(0), shuffle_roles=False)
    return engine, state


def test_distance_between_neighbors_is_one():
    _, state = new_state(5)
    assert distance(state, 0, 1) == 1
    assert distance(state, 0, 4) == 1


def test_distance_wraps_around_the_circle():
    _, state = new_state(8)
    assert distance(state, 0, 4) == 4
    assert distance(state, 1, 7) == 2


def test_distance_ignores_dead_players():
    _, state = new_state(6)
    state.players[1].life = 0
    # Seat 0 -> seat 2 agora e vizinho direto, pois o 1 esta morto
    assert distance(state, 0, 2) == 1


def test_valid_targets_for_shot_1_excludes_shooter():
    _, state = new_state(5)
    targets = valid_targets(state, 0, DiceFace.SHOT_1)
    assert 0 not in targets
    assert set(targets) == {1, 4}


def test_valid_targets_for_shot_2_reduces_to_one_with_three_alive():
    _, state = new_state(5)
    for seat in (1, 2):
        state.players[seat].life = 0
    targets = valid_targets(state, 0, DiceFace.SHOT_2)
    # So restam 0, 3 e 4 vivos: a distancia 2 vira 1
    assert set(targets) == {3, 4}


def test_valid_targets_for_beer_includes_self():
    _, state = new_state(4)
    targets = valid_targets(state, 0, DiceFace.BEER)
    assert 0 in targets
    assert set(targets) == {0, 1, 2, 3}
