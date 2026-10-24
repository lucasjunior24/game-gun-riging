import pytest

from app.engine.actions import (
    FINISH_TURN,
    RESOLVE,
    ROLL,
    STOP_ROLLING,
    WAIT_BOTS,
    allowed_actions,
    dice_targets,
)
from app.engine.dice import DiceFace
from app.engine.errors import RuleViolation
from app.engine.rules import Assignment, GameEngine
from app.engine.seating import valid_targets
from app.engine.state import GameStatus

from conftest import ScriptedRng, make_specs

SHOT_1 = DiceFace.SHOT_1
SHOT_2 = DiceFace.SHOT_2
DYNAMITE = DiceFace.DYNAMITE
BEER = DiceFace.BEER
ARROW = DiceFace.ARROW
GATLING = DiceFace.GATLING


def new_game(faces, total=5):
    engine = GameEngine()
    state = engine.new_game("g", make_specs(total), ScriptedRng(faces), shuffle_roles=False)
    return engine, state


def test_allowed_actions_por_fase():
    engine, state = new_game([GATLING] * 5 + [GATLING] * 2 + [GATLING] * 2)
    seat = state.turn.seat
    assert allowed_actions(state, seat) == [ROLL]

    engine.roll(state, seat)
    assert allowed_actions(state, seat) == [ROLL, STOP_ROLLING]

    engine.roll(state, seat, {0, 1})
    engine.roll(state, seat, {0, 1})
    # depois da terceira rolagem o motor ja entra em RESOLVENDO; sem dados de alvo, so encerrar
    assert allowed_actions(state, seat) == [FINISH_TURN]


def test_allowed_actions_com_dados_pendentes_pede_resolve():
    engine, state = new_game([SHOT_1, GATLING, GATLING, BEER, GATLING])
    seat = state.turn.seat
    engine.roll(state, seat)
    engine.stop_rolling(state, seat)
    assert allowed_actions(state, seat) == [RESOLVE]


def test_quem_nao_e_da_vez_espera_bots_ou_nada():
    engine, state = new_game([GATLING] * 5)
    # seat 0 (humano, Xerife) comeca: os bots nao tem acao
    assert allowed_actions(state, 1) == []
    state.turn.seat = 1
    assert allowed_actions(state, 0) == [WAIT_BOTS]


def test_partida_encerrada_nao_tem_acoes():
    engine, state = new_game([GATLING] * 5)
    state.status = GameStatus.DONE
    assert allowed_actions(state, state.turn.seat) == []


def test_dice_targets_bate_com_valid_targets():
    engine, state = new_game([SHOT_1, SHOT_2, BEER, GATLING, ARROW])
    seat = state.turn.seat
    engine.roll(state, seat)
    assert dice_targets(state, seat) == {}
    engine.stop_rolling(state, seat)

    targets = dice_targets(state, seat)
    assert set(targets) == {0, 1, 2}
    for index, seats in targets.items():
        assert seats == valid_targets(state, seat, state.turn.dice[index].face)


def test_version_sobe_a_cada_comando():
    engine, state = new_game([SHOT_1, GATLING, GATLING, GATLING, GATLING, GATLING])
    seat = state.turn.seat
    assert state.version == 0

    engine.roll(state, seat)
    assert state.version == 1
    engine.roll(state, seat, {4})
    assert state.version == 2
    engine.stop_rolling(state, seat)
    assert state.version == 3

    target = valid_targets(state, seat, SHOT_1)[0]
    new_state = engine.resolve(state, seat, [Assignment(0, target)])
    assert new_state.version == 4
    assert state.version == 3  # o original fica intacto


def test_comando_rejeitado_nao_sobe_version():
    engine, state = new_game([DYNAMITE, GATLING, GATLING, GATLING, GATLING])
    seat = state.turn.seat
    engine.roll(state, seat)
    with pytest.raises(RuleViolation):
        engine.roll(state, seat, {0})
    assert state.version == 1


def test_roll_rejeita_indice_repetido_ou_fora_da_faixa():
    engine, state = new_game([GATLING] * 5)
    seat = state.turn.seat
    engine.roll(state, seat)
    with pytest.raises(RuleViolation):
        engine.roll(state, seat, [1, 1])
    with pytest.raises(RuleViolation):
        engine.roll(state, seat, [5])
    with pytest.raises(RuleViolation):
        engine.roll(state, seat, [-1])


def test_eventos_tem_id_crescente_e_sem_buraco():
    engine, state = new_game([SHOT_1, SHOT_2, BEER, ARROW, GATLING, ARROW, ARROW])
    seat = state.turn.seat
    engine.roll(state, seat)
    engine.roll(state, seat, {3, 4})
    engine.stop_rolling(state, seat)
    assignments = [
        Assignment(index, valid_targets(state, seat, state.turn.dice[index].face)[0])
        for index in engine.pending_dice(state)
    ]
    state = engine.resolve(state, seat, assignments)

    ids = [event.id for event in state.events]
    assert ids == list(range(1, len(ids) + 1))
    assert state.next_event_id == len(ids) + 1
