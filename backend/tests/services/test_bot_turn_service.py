"""Testa o turno de bot no backend."""

import pytest

from app.dtos.character import IdentityDTO
from app.dtos.dice import UserBulletsDTO
from app.dtos.game_state import (
    CreateAuthoritativeGameDTO,
    ExecuteShotsCommandDTO,
    ShootDistanceCommandDTO,
)
from app.engine.dice import DiceFace
from app.services.game_service import GameService

from conftest import force_dice


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
    assert len(internal_state.events) > 0


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
    """A politica de tiro do bot usa a crenca construida a partir do historico do motor."""
    from app.services.policy_service import ShotPolicyService

    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    internal_state = service._games[state.game_id]
    internal_state.turn.seat = 1  # jogador 1 ataca o Xerife, levantando suspeita de fora da lei
    force_dice(
        service,
        state.game_id,
        [DiceFace.SHOT_1, DiceFace.ARROW, DiceFace.ARROW, DiceFace.ARROW, DiceFace.ARROW],
    )
    service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.players[1].user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name="Lucas", shots=1)],
                )
            ],
        ),
    )

    policy = ShotPolicyService(model_path="missing-shot-policy-model.pt")
    suspect_seat = 1
    neutral_seat = 4
    ranked = policy.rank_targets(internal_state, 0, [suspect_seat, neutral_seat])

    assert ranked[0] == suspect_seat


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
