"""Testa a aplicacao de tiro no backend."""

import pytest

from app.dtos.character import IdentityDTO, TeamDTO
from app.dtos.dice import UserBulletsDTO
from app.dtos.game_state import (
    CreateAuthoritativeGameDTO,
    ExecuteShotsCommandDTO,
    ShootDistanceCommandDTO,
)
from app.services.game_service import GameService


def test_shot_reduces_target_life():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    target = state.players[1]
    initial_bullet = target.bullet

    updated = service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.current_player.user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name=target.user_name, shots=2)],
                )
            ],
        ),
    )

    updated_target = next(p for p in updated.players if p.user_name == target.user_name)

    assert updated_target.bullet == initial_bullet - 2


def test_target_with_life_below_one_becomes_dead():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    target = state.players[1]

    updated = service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.current_player.user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name=target.user_name, shots=99)],
                )
            ],
        ),
    )

    assert not any(p.user_name == target.user_name for p in updated.players)


def test_dead_player_does_not_appear_as_available_target():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    target_name = state.players[2].user_name

    service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.current_player.user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name=target_name, shots=99)],
                )
            ],
        ),
    )

    public_state = service.get_state(state.game_id)
    for player in public_state.players:
        assert player.user_name != target_name


def test_shot_saves_game_action_history():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    target = state.players[1]
    initial_bullet = target.bullet

    service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.current_player.user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name=target.user_name, shots=2)],
                )
            ],
        ),
    )

    internal_state = service._games[state.game_id]
    assert len(internal_state.action_history) > 0

    action = internal_state.action_history[0]
    assert action.actor_user_name == "Lucas"
    assert action.target_user_name == target.user_name
    assert action.shots == 2
    assert action.target_life_before == initial_bullet
    assert action.target_life_after == initial_bullet - 2


def test_history_records_life_before_and_after():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    target = state.players[1]
    life_before = target.bullet

    service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.current_player.user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name=target.user_name, shots=3)],
                )
            ],
        ),
    )

    internal_state = service._games[state.game_id]
    action = internal_state.action_history[0]

    assert action.target_life_before == life_before
    assert action.target_life_after == life_before - 3


def test_winner_resolved_when_game_ends():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    updated = service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.players[1].user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name="Lucas", shots=99)],
                )
            ],
        ),
    )

    assert updated.status == "Done"
    assert updated.winner is not None
    assert updated.winner == TeamDTO.FORA_DA_LEI.value
