import pytest

from app.dtos.character import IdentityDTO
from app.dtos.history import ActionTypeDTO, GameActionHistoryDTO
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


def test_attack_on_revealed_sheriff_increases_outlaw_suspicion():
    service = BeliefService()
    actor = PlayerDTO(user_name="Bruno")
    sheriff = PlayerDTO(user_name="Ana", papel_probability={IdentityDTO.XERIFE.value: 1.0})
    action = GameActionHistoryDTO(
        game_id="game-1",
        actor_user_name="Bruno",
        action_type=ActionTypeDTO.TIRO,
        target_user_name="Ana",
        target_identity=IdentityDTO.XERIFE,
        shots=1,
    )

    service.update_beliefs_from_history([actor, sheriff], [action])

    assert actor.papel_probability.fora_da_lei > actor.papel_probability.assistente
    assert actor.papel_probability.fora_da_lei > 1.0 / 3.0
    assert actor.papel_probability.xerife == 0.0


def test_helping_revealed_sheriff_increases_assistant_suspicion():
    service = BeliefService()
    actor = PlayerDTO(user_name="Bruno")
    sheriff = PlayerDTO(user_name="Ana", papel_probability={IdentityDTO.XERIFE.value: 1.0})
    action = GameActionHistoryDTO(
        game_id="game-1",
        actor_user_name="Bruno",
        action_type=ActionTypeDTO.CERVEJA,
        target_user_name="Ana",
        target_identity=IdentityDTO.XERIFE,
    )

    service.update_beliefs_from_history([actor, sheriff], [action])

    assert actor.papel_probability.assistente > actor.papel_probability.fora_da_lei
    assert actor.papel_probability.assistente > 1.0 / 3.0
