import random

from app.bot.agent import BayesAgent
from app.bot.determinize import determinize
from app.bot.reroll import reroll_options
from app.dtos.game_state import DifficultyDTO
from app.engine.dice import DiceFace
from app.engine.state import TurnPhase
from app.engine.view import build_observation

from bot_helpers import ASSISTENTE, FORA_DA_LEI, RENEGADO, XERIFE, new_state, set_turn

ONE, TWO, BEER = DiceFace.SHOT_1, DiceFace.SHOT_2, DiceFace.BEER
ARROW, GATLING, DYNAMITE = DiceFace.ARROW, DiceFace.GATLING, DiceFace.DYNAMITE


def agent_with_seed(seed, n_samples=100):
    return BayesAgent(difficulty=DifficultyDTO.DIFICIL, seed=seed, n_samples=n_samples)


def rolling(state, seat, faces):
    set_turn(state, seat, faces, phase=TurnPhase.ROLLING, rolls_used=1)
    return build_observation(state, seat)


def test_opcoes_incluem_parar_e_nunca_rolam_dinamite():
    state = new_state(5)
    options = reroll_options(rolling(state, 2, [ONE, TWO, BEER, ARROW, DYNAMITE]))
    assert options[0] is None
    assert all(4 not in o for o in options[1:])
    assert len(options) == 1 + 15  # subconjuntos nao vazios de 4 faces distintas


def test_faces_iguais_viram_uma_opcao_so():
    state = new_state(5)
    options = reroll_options(rolling(state, 2, [ONE, ONE, ONE, ONE, ONE]))
    assert len(options) == 1 + 5  # rolar 1, 2, 3, 4 ou 5 dos "1"


def test_nao_rola_de_novo_gatling_com_tres_gatlings():
    state = new_state(5)
    decision = agent_with_seed(3).choose_reroll(rolling(state, 2, [GATLING, GATLING, GATLING, ARROW, TWO]))
    assert not decision.action or not ({0, 1, 2} & decision.action)


def test_com_vida_1_e_duas_dinamites_prefere_parar():
    state = new_state(5)
    state.players[2].life = 1
    decision = agent_with_seed(3).choose_reroll(rolling(state, 2, [DYNAMITE, DYNAMITE, BEER, ARROW, ONE]))
    assert decision.action is None
    assert "Parou" in decision.reason


def test_rola_de_novo_dados_inuteis():
    """Assistente com vida cheia: Cervejas nao servem para ele e o Xerife esta inteiro."""
    state = new_state(5)
    decision = agent_with_seed(3).choose_reroll(rolling(state, 4, [BEER, BEER, BEER, ONE, ONE]))
    assert decision.action and decision.action & {0, 1, 2}


def test_decisao_nao_depende_do_rng_real_da_partida():
    state = new_state(5)
    obs = rolling(state, 2, [ONE, TWO, BEER, ARROW, GATLING])
    a = agent_with_seed(7, n_samples=30).choose_reroll(obs)
    state.rng.seed(999_999)  # muda o futuro real
    b = agent_with_seed(7, n_samples=30).choose_reroll(build_observation(state, 2))
    assert a.action == b.action
    assert a.expected_utility == b.expected_utility


def test_determinizacao_usa_papeis_do_mundo_e_rng_proprio():
    state = new_state(5)
    obs = rolling(state, 2, [ONE, TWO, BEER, ARROW, GATLING])
    world = {0: XERIFE, 1: ASSISTENTE, 2: FORA_DA_LEI, 3: RENEGADO, 4: FORA_DA_LEI}
    rng = random.Random(1)

    sim = determinize(obs, world, rng)

    assert [p.identity for p in sim.players] == [world[s] for s in range(5)]
    assert [p.identity for p in sim.players] != [p.identity for p in state.players]
    assert sim.rng is rng and sim.rng is not state.rng
    assert [p.life for p in sim.players] == [p.life for p in state.players]
    assert [d.face for d in sim.turn.dice] == [d.face for d in state.turn.dice]
    assert sim.events == []
