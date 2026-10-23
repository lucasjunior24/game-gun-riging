"""Testa que o historico melhora o papel_probability no BeliefService."""

from app.dtos.character import IdentityDTO
from app.dtos.history import ActionTypeDTO, GameActionHistoryDTO
from app.dtos.players import IdentityProbabilityDTO, PlayerDTO
from app.services.belief_service import BeliefService


def test_player_that_shoots_revealed_sheriff_increases_outlaw_chance():
    service = BeliefService()

    actor = PlayerDTO(user_name="Bruno")
    sheriff = PlayerDTO(
        user_name="Lucas",
        papel_probability=IdentityProbabilityDTO.revealed_sheriff(),
    )
    action = GameActionHistoryDTO(
        game_id="game-1",
        actor_user_name="Bruno",
        action_type=ActionTypeDTO.TIRO,
        target_user_name="Lucas",
        target_identity=IdentityDTO.XERIFE,
        shots=1,
    )

    service.update_beliefs_from_history([actor, sheriff], [action])

    assert actor.papel_probability.fora_da_lei > actor.papel_probability.assistente
    assert actor.papel_probability.fora_da_lei > 1.0 / 3.0


def test_player_that_helps_sheriff_increases_assistant_chance():
    service = BeliefService()

    actor = PlayerDTO(user_name="Bruno")
    sheriff = PlayerDTO(
        user_name="Lucas",
        papel_probability=IdentityProbabilityDTO.revealed_sheriff(),
    )
    action = GameActionHistoryDTO(
        game_id="game-1",
        actor_user_name="Bruno",
        action_type=ActionTypeDTO.CERVEJA,
        target_user_name="Lucas",
        target_identity=IdentityDTO.XERIFE,
    )

    service.update_beliefs_from_history([actor, sheriff], [action])

    assert actor.papel_probability.assistente > actor.papel_probability.fora_da_lei
    assert actor.papel_probability.assistente > 1.0 / 3.0


def test_player_shooting_outlaw_suspect_increases_sheriff_ally_chance():
    service = BeliefService()

    high_outlaw = PlayerDTO(
        user_name="Suspeito",
        papel_probability=IdentityProbabilityDTO(
            fora_da_lei=0.9, renegado=0.1, assistente=0.0
        ),
    )
    actor = PlayerDTO(user_name="Bruno")
    sheriff = PlayerDTO(
        user_name="Lucas",
        papel_probability=IdentityProbabilityDTO.revealed_sheriff(),
    )
    action = GameActionHistoryDTO(
        game_id="game-1",
        actor_user_name="Bruno",
        action_type=ActionTypeDTO.TIRO,
        target_user_name="Suspeito",
        target_identity=IdentityDTO.FORA_DA_LEI,
        shots=1,
    )

    service.update_beliefs_from_history([actor, high_outlaw, sheriff], [action])

    assert (
        actor.papel_probability.assistente > actor.papel_probability.fora_da_lei
        or actor.papel_probability.assistente >= 1.0 / 3.0
    )


def test_probabilities_remain_normalized_after_multiple_actions():
    service = BeliefService()

    actor = PlayerDTO(user_name="Bruno")
    sheriff = PlayerDTO(
        user_name="Lucas",
        papel_probability=IdentityProbabilityDTO.revealed_sheriff(),
    )
    alice = PlayerDTO(user_name="Alice")

    actions = [
        GameActionHistoryDTO(
            game_id="game-1",
            actor_user_name="Bruno",
            action_type=ActionTypeDTO.TIRO,
            target_user_name="Lucas",
            target_identity=IdentityDTO.XERIFE,
            shots=1,
        ),
        GameActionHistoryDTO(
            game_id="game-1",
            actor_user_name="Alice",
            action_type=ActionTypeDTO.TIRO,
            target_user_name="Bruno",
            target_identity=IdentityDTO.FORA_DA_LEI,
            shots=1,
        ),
        GameActionHistoryDTO(
            game_id="game-1",
            actor_user_name="Bruno",
            action_type=ActionTypeDTO.TIRO,
            target_user_name="Alice",
            target_identity=IdentityDTO.ASSISTENTE,
            shots=1,
        ),
    ]

    service.update_beliefs_from_history([actor, sheriff, alice], actions)

    for player in [actor, alice]:
        assert abs(player.papel_probability.total() - 1.0) < 0.001


def test_hidden_player_not_gains_sheriff_probability_when_sheriff_known():
    service = BeliefService()
    sheriff_user_name = "Lucas"

    actor = PlayerDTO(user_name="Bruno")
    sheriff = PlayerDTO(
        user_name=sheriff_user_name,
        papel_probability=IdentityProbabilityDTO.revealed_sheriff(),
    )
    target = PlayerDTO(user_name="Alice")

    action = GameActionHistoryDTO(
        game_id="game-1",
        actor_user_name="Bruno",
        action_type=ActionTypeDTO.TIRO,
        target_user_name="Alice",
        target_identity=IdentityDTO.FORA_DA_LEI,
        shots=1,
    )

    service.update_beliefs_from_history(
        [actor, sheriff, target], [action], sheriff_user_name
    )

    assert actor.papel_probability.xerife == 0.0
    assert target.papel_probability.xerife == 0.0
