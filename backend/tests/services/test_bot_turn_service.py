"""Testa o turno de bot no backend."""

import pytest

from app.dtos.character import IdentityDTO
from app.dtos.dice import UserBulletsDTO
from app.dtos.game_state import (
    CreateAuthoritativeGameDTO,
    ExecuteShotsCommandDTO,
    ShootDistanceCommandDTO,
)
from app.services.game_service import GameService


def test_bot_executes_turn_without_frontend_action_history():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    service.finish_turn(state.game_id)
    bot_state = service.execute_bot_turn(state.game_id)

    assert bot_state.game_id == state.game_id
    assert bot_state.status in ("Running", "Done")


def test_bot_turn_generates_history():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    service.finish_turn(state.game_id)
    service.execute_bot_turn(state.game_id)

    internal_state = service._games[state.game_id]
    assert len(internal_state.action_history) > 0


def test_public_state_does_not_leak_beliefs_after_bot_turn():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    service.finish_turn(state.game_id)
    service.execute_bot_turn(state.game_id)

    public_state = service.get_state(state.game_id)
    for player in public_state.players:
        assert not hasattr(player, "papel_probability")
        assert not hasattr(player, "identity")
        assert not hasattr(player, "team")


def test_bot_turn_uses_belief_service():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    outlaw = state.players[1]
    service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=outlaw.user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name="Lucas", shots=1)],
                )
            ],
        ),
    )

    internal_state = service._games[state.game_id]
    internal_outlaw = next(
        p for p in internal_state.players if p.user_name == outlaw.user_name
    )

    assert internal_outlaw.papel_probability.fora_da_lei > 1.0 / 3.0
    assert abs(internal_outlaw.papel_probability.total() - 1.0) < 0.001


def test_turn_advances_after_bot_action():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    initial_turn = state.turn_number

    service.finish_turn(state.game_id)
    service.execute_bot_turn(state.game_id)

    public_state = service.get_state(state.game_id)
    assert public_state.turn_number > initial_turn


def test_error_when_calling_bot_turn_on_human_player():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    with pytest.raises(ValueError, match="nao e um bot"):
        service.execute_bot_turn(state.game_id)


def test_fallback_works_when_neural_model_does_not_exist():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    service.finish_turn(state.game_id)

    bot_state = service.execute_bot_turn(state.game_id)
    assert bot_state.status in ("Running", "Done")
    assert bot_state.game_id == state.game_id


def test_bot_turn_preserves_round_and_turn_state():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    service.finish_turn(state.game_id)
    bot_state = service.execute_bot_turn(state.game_id)

    assert bot_state.round_number >= 1
    assert bot_state.turn_number >= 1
    assert len(bot_state.players) > 0
