import random

import numpy as np

from app.bot.belief import infer
from app.engine.roles import team_for
from app.engine.rules import GameEngine
from app.engine.state import GameStatus
from app.engine.view import build_observation
from app.services.bot_turn_runner import BotTurnRunner
from app.sim.dataset import N_FEATURES, SEAT_FEATURES, featurize, marginals_of, record_game
from app.sim.runner import bot_specs, build_agents
from app.sim.train_value import group_split


def played_state(players=5, seed=0, turns=8):
    engine = GameEngine()
    state = engine.new_game("g", bot_specs(players), random.Random(seed), shuffle_roles=True)
    agents = build_agents(["heuristic"] * players, seed)
    for _ in range(turns):
        if state.status is GameStatus.DONE:
            break
        state = BotTurnRunner(engine, agents[state.turn.seat]).play_turn(state)
    return state


def features(state, seat):
    obs = build_observation(state, seat)
    return featurize(obs, marginals_of(infer(obs), obs))


def test_featurize_igual_para_estados_com_mesma_observacao():
    # troca papeis ocultos de lugar sem mudar nada publico: os atributos nao mudam
    swaps = 0
    for seed in range(20):
        state = played_state(seed=seed)
        for viewer in range(len(state.players)):
            hidden = [
                p for p in state.players if p.seat != viewer and p.public_identity is None
            ]
            pairs = [(a, b) for a in hidden for b in hidden if a.identity is not b.identity]
            if not pairs:
                continue
            before = features(state, viewer)
            a, b = pairs[0]
            a.identity, b.identity = b.identity, a.identity
            assert np.array_equal(before, features(state, viewer))
            a.identity, b.identity = b.identity, a.identity
            swaps += 1
    assert swaps > 10


def test_featurize_tem_tamanho_fixo_e_fica_entre_0_e_1():
    for players in (4, 5, 8):
        state = played_state(players)
        x = features(state, state.turn.seat)
        assert x.shape == (N_FEATURES,)
        assert x.min() >= 0.0 and x.max() <= 1.0


def test_assentos_que_nao_existem_ficam_zerados():
    x = features(played_state(4), 0)
    missing = N_FEATURES - 4 * SEAT_FEATURES  # 4 dos 8 assentos nao existem com 4 jogadores
    assert not x[missing:].any()


def test_rotulo_e_do_time_do_jogador_e_nao_de_quem_venceu():
    rows, result = record_game(5, 5, ["heuristic"] * 5)
    assert rows
    labels = {row["label"] for row in rows}
    assert labels == {0.0, 1.0}  # na mesma partida ha quem venceu e quem perdeu
    for row in rows:
        expected = team_for(result.roles[row["seat"]]) is result.winner  # 5 jogadores: 1 Renegado
        assert row["label"] == float(expected)


def test_split_por_partida_nao_mistura_grupos():
    groups = np.repeat(np.arange(50), 7)
    train_idx, val_idx = group_split(groups, 0.2, seed=1)
    assert set(groups[train_idx]).isdisjoint(groups[val_idx])
    assert len(train_idx) + len(val_idx) == len(groups)
    assert len(set(groups[val_idx])) == 10
