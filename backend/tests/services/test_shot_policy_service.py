from app.dtos.character import IdentityDTO
from app.dtos.dice import ExecuteDicesDTO, ExecuteDistanceDTO
from app.dtos.players import PlayerDTO
from app.services.policy_service import ShotPolicyService


def make_execution(*players: PlayerDTO) -> ExecuteDicesDTO:
    return ExecuteDicesDTO(
        game_id="game-1",
        current_player=PlayerDTO(user_name="Sheriff", bullet=3, arrow=0),
        current_identity=IdentityDTO.XERIFE.value,
        table_situation="test",
        one_distance=ExecuteDistanceDTO(
            bullet_total=2,
            players_options=list(players),
        ),
        two_distance=None,
    )


def test_sheriff_prioritizes_target_with_outlaw_belief_without_model():
    outlaw = PlayerDTO(
        user_name="Outlaw",
        position=1,
        bullet=3,
        arrow=0,
        papel_probability={
            IdentityDTO.FORA_DA_LEI.value: 0.9,
            IdentityDTO.RENEGADO.value: 0.1,
            IdentityDTO.ASSISTENTE.value: 0.0,
        },
    )
    assistant = PlayerDTO(
        user_name="Assistant",
        position=2,
        bullet=3,
        arrow=0,
        papel_probability={IdentityDTO.ASSISTENTE.value: 1.0},
    )
    service = ShotPolicyService(model_path="missing-shot-policy-model.pt")

    prediction = service.predict(make_execution(outlaw, assistant))

    assert prediction.decisions[0].target_user_name == "Outlaw"


def test_policy_does_not_choose_dead_or_current_player():
    current_player_option = PlayerDTO(
        user_name="Sheriff",
        position=1,
        bullet=3,
        is_alive=True,
        papel_probability={IdentityDTO.XERIFE.value: 1.0},
    )
    dead_outlaw = PlayerDTO(
        user_name="Dead",
        position=2,
        bullet=3,
        is_alive=False,
        papel_probability={IdentityDTO.FORA_DA_LEI.value: 1.0},
    )
    renegade = PlayerDTO(
        user_name="Renegade",
        position=3,
        bullet=3,
        is_alive=True,
        papel_probability={IdentityDTO.RENEGADO.value: 1.0},
    )
    service = ShotPolicyService(model_path="missing-shot-policy-model.pt")

    prediction = service.predict(
        make_execution(current_player_option, dead_outlaw, renegade)
    )

    assert prediction.decisions[0].target_user_name == "Renegade"


def test_apply_prediction_fills_user_bullets():
    target = PlayerDTO(
        user_name="Outlaw",
        position=1,
        bullet=3,
        papel_probability={IdentityDTO.FORA_DA_LEI.value: 1.0},
    )
    execution = make_execution(target)
    service = ShotPolicyService(model_path="missing-shot-policy-model.pt")

    prediction = service.predict(execution)
    result = service.apply_prediction(execution, prediction)

    assert result.one_distance.user_bullets[0].user_name == "Outlaw"
    assert result.one_distance.user_bullets[0].shots == 2
