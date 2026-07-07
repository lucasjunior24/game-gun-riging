"""Testa que o GameStateDTO não vaza campos internos."""

from app.dtos.character import IdentityDTO
from app.dtos.game_state import (
    CreateAuthoritativeGameDTO,
    PublicPlayerDTO,
)
from app.services.game_service import GameService


def test_game_state_does_not_return_papel_probability():
    service = GameService()

    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))

    for player in state.players:
        assert not hasattr(player, "papel_probability")


def test_game_state_does_not_return_hidden_identity():
    service = GameService()

    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))

    for player in state.players:
        assert not hasattr(player, "identity")


def test_sheriff_appears_with_revealed_identity():
    service = GameService()

    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))

    sheriff = state.players[0]
    assert sheriff.revealed_identity == IdentityDTO.XERIFE.value


def test_hidden_players_appear_with_none_revealed_identity():
    service = GameService()

    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))

    for player in state.players[1:]:
        assert player.revealed_identity is None


def test_public_state_preserves_life_arrows_bullets_and_character():
    service = GameService()

    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))

    for player in state.players:
        assert isinstance(player.user_id, int)
        assert isinstance(player.user_name, str)
        assert isinstance(player.bullet, int)
        assert isinstance(player.arrow, int)
        assert isinstance(player.is_alive, bool)
        assert isinstance(player.is_bot, bool)
        assert player.position > 0


def test_public_player_type_has_no_papel_probability_field():
    fields = list(PublicPlayerDTO.model_fields.keys())
    assert "papel_probability" not in fields
    assert "identity" not in fields
    assert "team" not in fields
