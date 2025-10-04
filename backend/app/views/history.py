from fastapi import APIRouter, Depends

from app.application_manager import ApplicationManager
from app.auth.token import get_token

from app.controllers.history import HistoryController
from app.dtos.dice import DiceShowDTO, ExecuteDicesDTO, UserBulletsDTO
from app.dtos.history import HistoryDTO
from app.dtos.message import MessageDTO
from app.dtos.response import (
    ResponseDTO,
    ResponseModelDTO,
)


history_router = APIRouter(
    prefix="/history",
    tags=["History"],
    dependencies=[Depends(get_token)],
    responses={404: {"description": "Not found"}},
)


@history_router.post("", response_model=ResponseModelDTO[HistoryDTO])
async def add(
    message: str,
):
    history_controller = ApplicationManager.get(HistoryController)
    message_dto = MessageDTO(message=message, author="lucas-sousa")
    history_dto = HistoryDTO(messages=[message_dto])
    data = history_controller.create(history_dto)
    return ResponseDTO(data=data, message="success")


@history_router.put("/messages", response_model=ResponseModelDTO[HistoryDTO])
async def add_messages(
    history_id: str,
    messages: list[str],
):
    history_controller = ApplicationManager.get(HistoryController)
    messages_dto = history_controller.create_messages_dto(messages)
    data = history_controller.add_messages(messages=messages_dto, history_id=history_id)
    return ResponseDTO(data=data, message="success")
