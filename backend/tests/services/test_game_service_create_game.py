"""Testa a criacao de partida pelo backend."""

from app.dtos.character import IdentityDTO
from app.dtos.game_state import CreateAuthoritativeGameDTO
from app.services.game_service import GameService


def test_create_game_with_correct_number_of_players():
    service = GameService()

    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=4)
    )

    assert len(state.players) == 4


def test_exactly_one_sheriff_exists():
    service = GameService()

    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    sheriff_count = sum(
        1 for p in state.players if p.revealed_identity == IdentityDTO.XERIFE.value
    )
    assert sheriff_count == 1


def test_sheriff_starts_with_xerife_probability_one():
    service = GameService()

    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    internal_state = service._games[state.game_id]
    sheriff = internal_state.players[0]
    assert sheriff.papel_probability.xerife == 1.0


def test_hidden_players_start_with_xerife_probability_zero():
    service = GameService()

    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    internal_state = service._games[state.game_id]
    for player in internal_state.players[1:]:
        assert player.papel_probability.xerife == 0.0


def test_hidden_players_probabilities_sum_to_one():
    service = GameService()

    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    internal_state = service._games[state.game_id]
    for player in internal_state.players[1:]:
        total = player.papel_probability.total()
        assert abs(total - 1.0) < 0.001


def test_first_state_returned_does_not_leak_internal_fields():
    service = GameService()

    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=5)
    )

    for player in state.players:
        assert not hasattr(player, "papel_probability")
        assert not hasattr(player, "identity")
        assert not hasattr(player, "team")


def test_game_has_status_running_after_creation():
    service = GameService()

    state = service.create_game(
        CreateAuthoritativeGameDTO(player_name="Lucas", players_total=3)
    )

    assert state.status == "Running"
    assert state.winner is None
