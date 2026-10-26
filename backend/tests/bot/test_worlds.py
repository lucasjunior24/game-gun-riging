from collections import Counter

from app.bot.worlds import enumerate_worlds
from app.engine.roles import ROLE_DISTRIBUTION
from app.engine.view import build_observation

from bot_helpers import RENEGADO, XERIFE, kill, new_state


def test_cinco_jogadores_bot_fora_da_lei_tem_6_mundos():
    worlds = enumerate_worlds(build_observation(new_state(5), 2))
    assert len(worlds) == 6


def test_oito_jogadores_bot_xerife_tem_210_mundos():
    worlds = enumerate_worlds(build_observation(new_state(8), 0))
    assert len(worlds) == 210


def test_mundos_nao_se_repetem():
    worlds = enumerate_worlds(build_observation(new_state(8), 0))
    assert len({tuple(sorted(w.items(), key=lambda kv: kv[0])) for w in worlds}) == 210


def test_morto_revelado_fixa_o_papel_em_todos_os_mundos():
    state = new_state(5)
    kill(state, 1)  # o Renegado morre e revela o papel
    worlds = enumerate_worlds(build_observation(state, 2))
    assert all(w[1] is RENEGADO for w in worlds)
    assert len(worlds) == 2  # sobram FL e Assistente para os assentos 3 e 4


def test_xerife_e_o_proprio_papel_sao_fixos():
    state = new_state(6)
    obs = build_observation(state, 3)
    for world in enumerate_worlds(obs):
        assert world[0] is XERIFE
        assert world[3] is obs.my_identity


def test_todo_mundo_respeita_a_contagem_de_papeis():
    for total in range(4, 9):
        for viewer in range(total):
            for world in enumerate_worlds(build_observation(new_state(total), viewer)):
                assert Counter(world.values()) == Counter(ROLE_DISTRIBUTION[total])
