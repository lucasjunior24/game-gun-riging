from fastapi import APIRouter, Depends

from app.application_manager import ApplicationManager
from app.auth.token import get_token

from app.controllers.chat import ChatController
from app.dtos.dice import (
    DiceShowDTO,
    ExecuteDicesDTO,
    ExecuteDistanceDTO,
    ListShotsDTO,
    UserBulletsDTO,
)
from app.dtos.response import (
    ResponseDTO,
    ResponseModelDTO,
)
from app.services.policy_service import ShotPolicyService

dices_router = APIRouter(
    prefix="/dices",
    tags=["Dices"],
    dependencies=[Depends(get_token)],
    responses={404: {"description": "Not found"}},
)


@dices_router.put("/valid", response_model=ResponseModelDTO[list[DiceShowDTO]])
async def valide_dices(
    dices: list[DiceShowDTO],
):
    new_dices: list[DiceShowDTO] = []
    for dice in dices:
        if dice.dice in [1, 2]:
            new_dices.append(DiceShowDTO(dice=dice.dice, locked=True, show=dice.show))
        else:
            new_dices.append(dice)
    return ResponseDTO(data=new_dices, message="success")


@dices_router.put("/execution", response_model=ResponseModelDTO[ExecuteDicesDTO])
async def execution_dices(
    execution: ExecuteDicesDTO,
):
    shot_policy_service = ShotPolicyService()
    prediction = shot_policy_service.predict(execution)
    execution_result = shot_policy_service.apply_prediction(execution, prediction)

    return ResponseDTO(data=execution_result, message="success")
