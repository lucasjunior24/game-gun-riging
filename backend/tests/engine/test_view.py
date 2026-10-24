import random
from dataclasses import FrozenInstanceError

import pytest

from app.dtos.character import IdentityDTO
from app.engine.rules import GameEngine
from app.engine.state import GameStatus
from app.engine.view import build_observation
from app.services.bot_turn_runner import BotTurnRunner
from app.services.policy_service import ShotPolicyService

from conftest import make_specs


def assert_no_hidden_role_leak(state, viewer):
    obs = build_observation(state, viewer)
    assert obs.my_identity is state.players[viewer].identity
    for p in obs.players:
        real = state.players[p.seat]
        if real.identity is IdentityDTO.XERIFE or not real.is_alive:
            assert p.public_identity is real.identity
        else:
            assert p.public_identity is None
    for event in obs.events:
        for seat, shown in (
            (event.actor_seat, event.actor_public_identity),
            (event.target_seat, event.target_public_identity),
        ):
            if shown is not None:
                real = state.players[seat]
                assert real.identity is IdentityDTO.XERIFE or not real.is_alive


def test_observacao_nao_revela_papel_oculto_de_outros():
    engine = GameEngine()
    state = engine.new_game("g", make_specs(5), random.Random(1), shuffle_roles=True)
    for viewer in range(5):
        obs = build_observation(state, viewer)
        for p in obs.players:
            if p.seat == viewer:
                continue
            real = state.players[p.seat].identity
            if real is IdentityDTO.XERIFE:
                assert p.public_identity is IdentityDTO.XERIFE
            else:
                assert p.public_identity is None


def test_observacao_traz_o_proprio_papel():
    engine = GameEngine()
    state = engine.new_game("g", make_specs(5), random.Random(2), shuffle_roles=True)
    for viewer in range(5):
        assert build_observation(state, viewer).my_identity is state.players[viewer].identity


def test_morto_revela_papel_na_observacao():
    engine = GameEngine()
    state = engine.new_game("g", make_specs(5), random.Random(3), shuffle_roles=False)
    dead = state.players[2]
    engine._damage(state, None, dead.seat, dead.life)

    obs = build_observation(state, 0)
    snapshot = obs.players[dead.seat]
    assert not snapshot.is_alive
    assert snapshot.public_identity is dead.identity
    assert snapshot.distance_from_viewer is None


def test_distancia_considera_so_vivos():
    engine = GameEngine()
    state = engine.new_game("g", make_specs(5), random.Random(4), shuffle_roles=False)
    engine._damage(state, None, 1, state.players[1].life)

    obs = build_observation(state, 0)
    assert obs.players[2].distance_from_viewer == 1
    assert obs.players[0].distance_from_viewer == 0


def test_observacao_e_imutavel():
    engine = GameEngine()
    state = engine.new_game("g", make_specs(4), random.Random(5))
    obs = build_observation(state, 0)
    with pytest.raises(FrozenInstanceError):
        obs.players[0].life = 99


def test_propriedade_nenhuma_observacao_vaza_papel_em_partidas_inteiras():
    engine = GameEngine()
    runner = BotTurnRunner(engine, ShotPolicyService(model_path="missing-shot-policy-model.pt"))
    for seed in range(200):
        total = 4 + seed % 5
        state = engine.new_game(
            "g", make_specs(total, all_bots=True), random.Random(seed), shuffle_roles=True
        )
        for _ in range(500):
            for viewer in range(total):
                assert_no_hidden_role_leak(state, viewer)
            if state.status is GameStatus.DONE:
                break
            state = runner.play_turn(state)
        assert state.status is GameStatus.DONE, f"seed {seed} nao terminou"
