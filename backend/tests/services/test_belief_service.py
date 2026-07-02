import pytest

from app.dtos.character import IdentityDTO
from app.dtos.players import PlayerDTO
from app.services.belief_service import BeliefService


def test_initialize_revealed_sheriff_as_certain_identity():
    service = BeliefService()
    player = PlayerDTO(user_name="Ana")

    beliefs = service.initialize_player_belief(player, sheriff_user_name="Ana")

    assert beliefs.probability_for(IdentityDTO.XERIFE) == 1.0
    assert beliefs.probability_for(IdentityDTO.FORA_DA_LEI) == 0.0
    assert beliefs.probability_for(IdentityDTO.RENEGADO) == 0.0
    assert beliefs.probability_for(IdentityDTO.ASSISTENTE) == 0.0


def test_initialize_hidden_player_without_sheriff_probability_when_sheriff_is_known():
    service = BeliefService()
    player = PlayerDTO(user_name="Bruno")

    beliefs = service.initialize_player_belief(player, sheriff_user_name="Ana")

    assert beliefs.probability_for(IdentityDTO.XERIFE) == 0.0
    assert beliefs.total() == pytest.approx(1.0)
    assert beliefs.probability_for(IdentityDTO.FORA_DA_LEI) > 0
    assert beliefs.probability_for(IdentityDTO.RENEGADO) > 0
    assert beliefs.probability_for(IdentityDTO.ASSISTENTE) > 0


def test_parse_probabilities_validates_identity_with_enum():
    service = BeliefService()

    with pytest.raises(ValueError):
        service.parse_probabilities({"vice": 1.0})


def test_player_accepts_legacy_float_probability_as_empty_belief():
    player = PlayerDTO(user_name="Bruno", papel_probability=0.7)

    assert player.papel_probability.total() == 0.0
