import copy
import random

import pytest

from app.engine.dice import DiceFace
from app.engine.errors import RuleViolation
from app.engine.rules import Assignment, GameEngine
from app.engine.state import GameStatus, TurnPhase

from conftest import make_specs

SHOT_1 = DiceFace.SHOT_1
SHOT_2 = DiceFace.SHOT_2
BEER = DiceFace.BEER
GATLING = DiceFace.GATLING
DYNAMITE = DiceFace.DYNAMITE
FILLER = DiceFace.ARROW


def resolving_state(faces, total=5, life=4):
    engine = GameEngine()
    state = engine.new_game("g", make_specs(total, life=life), random.Random(0), shuffle_roles=False)
    for index, face in enumerate(faces):
        state.turn.dice[index].face = face
        state.turn.dice[index].locked = face is DYNAMITE
    state.turn.rolls_used = 1
    state.turn.phase = TurnPhase.RESOLVING
    return engine, state


def test_shot_1_damages_target_at_distance_one():
    engine, state = resolving_state([SHOT_1, FILLER, FILLER, FILLER, FILLER])
    seat = state.turn.seat
    target = (seat + 1) % len(state.players)
    before = state.players[target].life

    result = engine.resolve(state, seat, [Assignment(dice_index=0, target_seat=target)])

    assert result.players[target].life == before - 1


def test_shot_out_of_range_is_rejected_without_mutating_state():
    engine, state = resolving_state([SHOT_2, FILLER, FILLER, FILLER, FILLER], total=6)
    seat = state.turn.seat
    out_of_range = (seat + 1) % len(state.players)  # distancia 1, nao 2
    before = copy.deepcopy(state.players)

    with pytest.raises(RuleViolation):
        engine.resolve(state, seat, [Assignment(dice_index=0, target_seat=out_of_range)])

    assert state.players == before


def test_beer_heals_but_never_above_max_life():
    engine, state = resolving_state([BEER, FILLER, FILLER, FILLER, FILLER])
    seat = state.turn.seat
    state.players[seat].life = state.players[seat].max_life

    result = engine.resolve(state, seat, [Assignment(dice_index=0, target_seat=seat)])

    assert result.players[seat].life == result.players[seat].max_life


def test_gatling_hits_everyone_but_the_shooter_once():
    engine, state = resolving_state([GATLING, GATLING, GATLING, GATLING, GATLING], total=5)
    seat = state.turn.seat
    before = {p.seat: p.life for p in state.players}

    result = engine.resolve(state, seat, [])

    for player in result.players:
        if player.seat == seat:
            assert player.life == before[player.seat]
        else:
            assert player.life == before[player.seat] - 1


def test_resolution_order_is_shot_1_then_shot_2_then_beer():
    engine, state = resolving_state([SHOT_1, SHOT_2, BEER, FILLER, FILLER], total=6)
    seat = state.turn.seat
    one_target = (seat + 1) % 6
    two_target = (seat + 2) % 6

    with pytest.raises(RuleViolation):
        engine.resolve_one(state, seat, Assignment(dice_index=2, target_seat=seat))

    result = engine.resolve_one(state, seat, Assignment(dice_index=0, target_seat=one_target))
    result = engine.resolve_one(result, seat, Assignment(dice_index=1, target_seat=two_target))
    result = engine.resolve_one(result, seat, Assignment(dice_index=2, target_seat=seat))
    assert result.turn.seat != seat


def test_resolve_requires_exactly_one_assignment_per_pending_die():
    engine, state = resolving_state([SHOT_1, SHOT_1, BEER, FILLER, FILLER], total=5)
    seat = state.turn.seat
    target = (seat + 1) % 5

    with pytest.raises(RuleViolation):
        engine.resolve(state, seat, [Assignment(dice_index=0, target_seat=target)])


def test_death_during_resolution_updates_distance_for_the_next_die():
    engine, state = resolving_state([SHOT_1, SHOT_1, FILLER, FILLER, FILLER], total=4, life=1)
    seat = state.turn.seat
    neighbor = (seat + 1) % 4
    far_player = (seat + 2) % 4

    result = engine.resolve_one(state, seat, Assignment(dice_index=0, target_seat=neighbor))
    assert result.players[neighbor].is_alive is False

    # Com o vizinho morto, o jogador "distante" agora fica a distancia 1
    result = engine.resolve_one(result, seat, Assignment(dice_index=1, target_seat=far_player))
    assert result.players[far_player].is_alive is False


def test_resolving_without_pending_dice_still_advances_turn():
    engine, state = resolving_state([GATLING, FILLER, FILLER, FILLER, FILLER], total=5)
    seat = state.turn.seat

    result = engine.resolve(state, seat, [])

    assert result.turn.seat != seat
