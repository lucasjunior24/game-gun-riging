from fastapi import APIRouter, Depends

from app.auth.token import get_token

from app.dtos.dice import DiceShowDTO, ExecuteDicesDTO, UserBulletsDTO
from app.dtos.response import (
    ResponseDTO,
    ResponseModelDTO,
)


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
    print(execution.current_player.user_name)
    for bullet in range(0, execution.one_distance.bullet_total):
        player = execution.one_distance.players_options[0]
        if execution.one_distance.user_bullets:
            execution.one_distance.user_bullets[0].shoots += 1
        else:
            user = UserBulletsDTO(user_name=player.user_name, shoots=1)
            execution.one_distance.user_bullets.append(user)
    if execution.two_distance:
        for bullet in range(0, execution.two_distance.bullet_total):
            player = execution.two_distance.players_options[0]
            if execution.two_distance.user_bullets:
                execution.two_distance.user_bullets[0].shoots += 1
            else:
                user = UserBulletsDTO(user_name=player.user_name, shoots=1)
                execution.two_distance.user_bullets.append(user)
    return ResponseDTO(data=execution)
