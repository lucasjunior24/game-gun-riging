import pytest

from app.bot.belief import infer
from app.bot.evaluation import Evaluator, evaluate, relation
from app.engine.events import EventType
from app.engine.view import build_observation

from bot_helpers import ASSISTENTE, FORA_DA_LEI, RENEGADO, XERIFE, add_event, kill, new_state


def roles(state):
    return {p.seat: p.identity for p in state.players}


def test_vitoria_vale_1_e_derrota_menos_1():
    state = new_state(5)
    for seat in (1, 2, 3):  # Renegado e Foras da lei mortos: vitoria do Xerife
        kill(state, seat)
    world = roles(state)
    assert evaluate(state, world, 0) == 1.0
    assert evaluate(state, world, 4) == 1.0
    assert evaluate(state, world, 2) == -1.0
    assert evaluate(state, world, 1) == -1.0


def test_vitoria_segue_os_papeis_do_mundo_e_nao_do_estado():
    state = new_state(5)
    for seat in (1, 2, 3):
        kill(state, seat)
    assert evaluate(state, roles(state), 0) == 1.0  # mundo real: so Xerife e Assistente vivos
    world = roles(state)
    world[1], world[4] = ASSISTENTE, RENEGADO  # outro mundo: o vivo no assento 4 e o Renegado
    assert -1 < evaluate(state, world, 0) < 1


def test_partida_em_andamento_fica_dentro_de_menos_1_e_1():
    state = new_state(8)
    for p in state.players:
        p.arrows = 3
    for seat in range(8):
        assert -1 < evaluate(state, roles(state), seat) < 1


def test_dano_no_inimigo_e_bom_e_no_aliado_e_ruim():
    state = new_state(5)
    world = roles(state)
    base = evaluate(state, world, 0)
    state.players[2].life -= 1  # Fora da lei
    assert evaluate(state, world, 0) > base
    state.players[2].life += 1
    state.players[4].life -= 1  # Assistente
    assert evaluate(state, world, 0) < base


def test_renegado_quer_xerife_vivo_com_outros_vivos():
    assert relation(RENEGADO, XERIFE, renegade_endgame=False) > 0
    state = new_state(5)
    world = roles(state)
    base = evaluate(state, world, 1)
    state.players[0].life -= 3
    assert evaluate(state, world, 1) < base


def test_renegado_ataca_xerife_quando_so_restam_os_dois():
    assert relation(RENEGADO, XERIFE, renegade_endgame=True) < 0
    state = new_state(5)
    for seat in (2, 3, 4):
        kill(state, seat)
    world = roles(state)
    base = evaluate(state, world, 1)
    state.players[0].life -= 3
    assert evaluate(state, world, 1) > base


def test_fora_da_lei_comemora_morte_do_xerife():
    state = new_state(5)
    kill(state, 0)
    assert evaluate(state, roles(state), 2) == 1.0
    assert evaluate(state, roles(state), 1) == -1.0  # Renegado perde: ainda ha outros vivos


def test_evaluator_e_a_media_exata_sobre_os_mundos():
    state = new_state(6)
    add_event(state, EventType.SHOT, actor=3, target=0, options=[0, 2])
    kill(state, 5)
    state.players[2].life = 1
    state.players[4].arrows = 2
    for viewer in (0, 1, 2, 4):
        belief = infer(build_observation(state, viewer))
        exact = sum(
            p * evaluate(state, w, viewer) for w, p in zip(belief.worlds, belief.probabilities())
        )
        assert Evaluator(belief, viewer).value(state) == pytest.approx(exact)


def test_flechas_pesam_contra_mim():
    state = new_state(5)
    world = roles(state)
    base = evaluate(state, world, 2)
    state.players[2].arrows = 3
    assert evaluate(state, world, 2) < base
    assert relation(FORA_DA_LEI, FORA_DA_LEI, renegade_endgame=False) > 0
