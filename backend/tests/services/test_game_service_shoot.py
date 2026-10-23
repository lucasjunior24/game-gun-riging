"""Testa a aplicacao de tiro no backend."""

from app.dtos.character import TeamDTO
from app.dtos.dice import UserBulletsDTO
from app.dtos.game_state import (
    CreateAuthoritativeGameDTO,
    ExecuteShotsCommandDTO,
    ShootDistanceCommandDTO,
)
from app.engine.dice import DiceFace
from app.services.game_service import GameService
from app.services.history_adapter import events_to_history

from conftest import force_dice

FILLER = DiceFace.ARROW


def shoot(service, game_id, actor_user_id, target_name, dice_count=1):
    faces = [DiceFace.SHOT_1] * dice_count + [FILLER] * (5 - dice_count)
    force_dice(service, game_id, faces)
    return service.execute_shots(
        game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=actor_user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name=target_name, shots=dice_count)],
                )
            ],
        ),
    )


def test_shot_reduces_target_life():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    target = state.players[1]
    initial_bullet = target.bullet

    updated = shoot(service, state.game_id, state.current_player.user_id, target.user_name, dice_count=2)

    updated_target = next(p for p in updated.players if p.user_name == target.user_name)
    assert updated_target.bullet == initial_bullet - 2


def test_target_with_life_below_one_becomes_dead():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    target = state.players[1]
    service._games[state.game_id].players[1].life = 1

    updated = shoot(service, state.game_id, state.current_player.user_id, target.user_name, dice_count=1)

    updated_target = next(p for p in updated.players if p.user_name == target.user_name)
    assert updated_target.is_alive is False


def test_dead_player_stays_visible_as_not_alive():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    target_name = state.players[1].user_name
    service._games[state.game_id].players[1].life = 1

    shoot(service, state.game_id, state.current_player.user_id, target_name, dice_count=1)

    public_state = service.get_state(state.game_id)
    target = next(p for p in public_state.players if p.user_name == target_name)
    assert target.is_alive is False
    # O jogador morto continua na lista (revela o papel), nao e removido.
    assert target.revealed_identity is not None


def test_shot_saves_game_action_history():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    target = state.players[1]

    shoot(service, state.game_id, state.current_player.user_id, target.user_name, dice_count=2)

    internal_state = service._games[state.game_id]
    history = events_to_history(internal_state)
    shots_on_target = [
        a for a in history if a.action_type == "TIRO" and a.target_user_name == target.user_name
    ]
    assert len(shots_on_target) == 2
    assert all(a.actor_user_name == "Lucas" for a in shots_on_target)


def test_life_decreases_by_one_per_shot_die():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    target = state.players[1]
    life_before = target.bullet

    updated = shoot(service, state.game_id, state.current_player.user_id, target.user_name, dice_count=3)

    updated_target = next(p for p in updated.players if p.user_name == target.user_name)
    assert updated_target.bullet == life_before - 3


def test_winner_resolved_when_game_ends():
    service = GameService()
    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    internal_state = service._games[state.game_id]
    internal_state.turn.seat = 1  # e a vez do jogador 1
    internal_state.players[0].life = 1  # deixa o Xerife a um tiro da morte

    updated = shoot(service, state.game_id, state.players[1].user_id, "Lucas", dice_count=1)

    assert updated.status == "Done"
    assert updated.winner == TeamDTO.FORA_DA_LEI.value
