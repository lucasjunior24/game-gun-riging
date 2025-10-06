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
    chat_controller = ChatController()

    if execution.one_distance.bullet_total:
        teste_message = chat_controller.exec_bullets_chat(
            execution.one_distance,
            execution.current_identity,
            execution.current_player.user_name,
            "1",
        )

        response_one = chat_controller.add_message(
            new_message=teste_message,
            table_situation=execution.table_situation,
            game_id=execution.game_id,
        )
        shots_one = ListShotsDTO(**response_one)
        for shot in shots_one.shots_list:
            shot_one = UserBulletsDTO(**shot.model_dump(mode="json"))
            execution.one_distance.user_bullets.append(shot_one)

    if execution.two_distance:
        message_two = chat_controller.exec_bullets_chat(
            execution.two_distance,
            execution.current_identity,
            execution.current_player.user_name,
            "2",
        )
        data = chat_controller.add_message(
            new_message=message_two,
            table_situation=execution.table_situation,
            game_id=execution.game_id,
        )
        shots_two = ListShotsDTO(**data)
        for shot in shots_two.shots_list:
            shot_two = UserBulletsDTO(**shot.model_dump(mode="json"))
            execution.two_distance.user_bullets.append(shot_two)

    return ResponseDTO(data=execution)


# def exec_bullets(
#     execution: ExecuteDistanceDTO, personagem: str, user_name: str
# ) -> ExecuteDistanceDTO:

#     for bullet in range(0, execution.bullet_total):
#         player = execution.players_options[0]
#         if execution.user_bullets:
#             execution.user_bullets[0].shoots += 1
#         else:
#             user = UserBulletsDTO(user_name=player.user_name, shoots=1)
#             execution.user_bullets.append(user)

#     return execution
