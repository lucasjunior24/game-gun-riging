import random
import time
from itertools import permutations

import pytest

from app.bot.agent import BayesAgent
from app.bot.selection import pick, softmax
from app.dtos.character import IdentityDTO
from app.dtos.game_state import CreateAuthoritativeGameDTO, DifficultyDTO
from app.dtos.game_view import AdvanceBotsCommandDTO
from app.engine.dice import DiceFace
from app.engine.rules import GameEngine
from app.engine.state import GameStatus, TurnPhase
from app.engine.view import build_observation
from app.services.bot_turn_runner import BotTurnRunner
from app.services.game_service import GameService

from bot_helpers import new_state, set_turn

ONE, TWO, BEER = DiceFace.SHOT_1, DiceFace.SHOT_2, DiceFace.BEER
ARROW, GATLING = DiceFace.ARROW, DiceFace.GATLING


def agent_with_seed(seed):
    return BayesAgent(difficulty=DifficultyDTO.MEDIO, seed=seed, n_samples=20)


def played_state(total, seed, turns=6):
    """Uma partida com historia: alguns turnos jogados pelos proprios bots."""
    engine = GameEngine()
    state = new_state(total, seed=seed)
    runner = BotTurnRunner(engine, BayesAgent(engine, seed=seed, n_samples=4))
    for _ in range(turns):
        if state.status is GameStatus.DONE:
            break
        state = runner.play_turn(state)
    return state


def compatible_permutations(state, viewer):
    """Trocas de papel entre ocultos vivos: nada publico muda."""
    hidden = [
        p.seat
        for p in state.players
        if p.is_alive and p.seat != viewer and p.identity is not IdentityDTO.XERIFE
    ]
    roles = [state.players[s].identity for s in hidden]
    for perm in sorted(set(permutations(roles)), key=lambda r: [x.value for x in r]):
        alt = state.clone()
        for seat, role in zip(hidden, perm):
            alt.players[seat].identity = role
        yield alt


@pytest.mark.parametrize("total,seed", [(5, 1), (6, 2), (8, 3)])
def test_decisao_invariante_a_papeis_ocultos(total, seed):
    """Se troco os papeis ocultos de lugar sem mudar nada publico, a decisao e a mesma."""
    state = played_state(total, seed)
    assert state.status is GameStatus.RUNNING
    viewer = next(
        p.seat for p in state.players if p.is_alive and p.identity is not IdentityDTO.XERIFE
    )
    for p in state.players:
        if p.is_alive:
            p.life = max(1, p.life - 2)

    set_turn(state, viewer, [ONE, TWO, BEER, BEER, ARROW])
    resolving = build_observation(state, viewer)
    expected_plan = agent_with_seed(1).choose_assignments(resolving).action

    set_turn(state, viewer, [ONE, TWO, BEER, ARROW, GATLING], phase=TurnPhase.ROLLING)
    rolling = build_observation(state, viewer)
    expected_reroll = agent_with_seed(1).choose_reroll(rolling).action

    checked = 0
    for alt in compatible_permutations(state, viewer):
        assert build_observation(alt, viewer) == rolling
        assert agent_with_seed(1).choose_reroll(rolling).action == expected_reroll
        set_turn(alt, viewer, [ONE, TWO, BEER, BEER, ARROW])
        alt_obs = build_observation(alt, viewer)
        assert alt_obs == resolving
        assert agent_with_seed(1).choose_assignments(alt_obs).action == expected_plan
        checked += 1
    assert checked > 1


def test_decisao_em_menos_de_300ms_com_8_jogadores():
    state = played_state(8, seed=4, turns=4)
    viewer = state.turn.seat
    for p in state.players:
        if p.is_alive:
            p.life = max(1, p.life - 2)
    agent = BayesAgent(difficulty=DifficultyDTO.DIFICIL, seed=0)

    set_turn(state, viewer, [ONE, TWO, BEER, ARROW, GATLING], phase=TurnPhase.ROLLING)
    obs = build_observation(state, viewer)
    agent.choose_reroll(obs)  # aquece caches de import
    start = time.perf_counter()
    agent.choose_reroll(obs)
    reroll_time = time.perf_counter() - start

    set_turn(state, viewer, [ONE, ONE, TWO, BEER, BEER])
    obs = build_observation(state, viewer)
    start = time.perf_counter()
    agent.choose_assignments(obs)
    assign_time = time.perf_counter() - start

    assert reroll_time < 0.3
    assert assign_time < 0.3


def test_decisao_traz_motivo_e_confianca():
    state = new_state(5)
    set_turn(state, 2, [TWO, ARROW, ARROW, GATLING, DiceFace.DYNAMITE])
    decision = agent_with_seed(0).choose_assignments(build_observation(state, 2))
    assert "2 em P0 (Xerife 100%)" in decision.reason
    assert 0 < decision.confidence <= 1
    assert decision.alternatives[0][1] >= decision.alternatives[-1][1]


def test_temperatura_zero_e_argmax_e_alta_e_quase_uniforme():
    assert softmax([0.1, 0.2, 0.15], 0) == [0.0, 1.0, 0.0]
    probs = softmax([0.1, 0.2, 0.15], 100)
    assert max(probs) - min(probs) < 0.01
    choice = pick([("a", 0.1), ("b", 0.2)], 0, random.Random(0))
    assert choice.action == "b" and choice.confidence == 1.0


def test_dificuldade_muda_quanto_o_bot_erra():
    state = new_state(5)
    set_turn(state, 2, [TWO, ARROW, ARROW, GATLING, DiceFace.DYNAMITE])
    obs = build_observation(state, 2)

    def sheriff_rate(difficulty):
        agent = BayesAgent(difficulty=difficulty, seed=0)
        hits = sum(agent.choose_assignments(obs).action[0].target_seat == 0 for _ in range(200))
        return hits / 200

    assert sheriff_rate(DifficultyDTO.DIFICIL) > sheriff_rate(DifficultyDTO.FACIL)
    assert sheriff_rate(DifficultyDTO.DIFICIL) > 0.95


def test_servico_usa_a_dificuldade_e_grava_o_motivo_nos_eventos():
    service = GameService()
    created = service.create_game(
        CreateAuthoritativeGameDTO(
            player_name="Lucas", players_total=5, difficulty=DifficultyDTO.DIFICIL
        )
    )
    assert service._difficulties[created.game_id] is DifficultyDTO.DIFICIL

    service.legacy_finish_turn(created.game_id)
    state = service._games[created.game_id]
    view = service.advance_bots(
        created.game_id, AdvanceBotsCommandDTO(expected_version=state.version)
    )

    bot_events = [e for e in view.events if e.type in ("TIRO", "CERVEJA", "DADO_ROLADO")]
    assert any("reason" in e.data for e in bot_events)
    for e in bot_events:
        if "reason" in e.data:
            assert 0 < e.data["confidence"] <= 1
