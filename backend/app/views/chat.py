from app.controllers.chat import ChatController
from fastapi import APIRouter

from app.dtos.character import IdentityDTO
from app.dtos.dice import DiceShowDTO
from app.dtos.response import (
    ResponseDTO,
    ResponseModelDTO,
)

from app.util.requestsDTOs.chat import ChatDTO

chat_ai_router = APIRouter(
    prefix="/chat_ai",
    tags=["Chat AI"],
    responses={404: {"description": "Not found"}},
)


@chat_ai_router.get("/all", response_model=ResponseModelDTO[list[ChatDTO]])
async def get_all():
    chat_controller = ChatController()
    chats = chat_controller.get_all()
    return ResponseDTO(data=chats, message="success")


@chat_ai_router.post(
    "/message",
    responses={201: {"model": ResponseModelDTO[ChatDTO]}},
    response_model=ResponseModelDTO[ChatDTO],
)
async def message(message: str, chat_id: str | None = None):
    chat_controller = ChatController()
    data = chat_controller.add_message(new_message=message, chat_id=chat_id)
    return ResponseDTO(data=data)


@chat_ai_router.post(
    "/execute",
    responses={201: {"model": ResponseModelDTO[ChatDTO]}},
    response_model=ResponseModelDTO[ChatDTO],
)
async def execute(
    dices: list[DiceShowDTO],
    identity: IdentityDTO = IdentityDTO.ASSISTENTE,
    chat_id: str | None = None,
):
    chat_controller = ChatController()
    data = chat_controller.formart_to_execure_dices(
        chat_id=chat_id, dices=dices, identity=identity
    )
    return ResponseDTO(data=data)


@chat_ai_router.post(
    "/band",
    responses={201: {"model": ResponseModelDTO[ChatDTO]}},
    response_model=ResponseModelDTO[ChatDTO],
)
async def band(message: str, chat_id: str | None = None):
    chat_controller = ChatController()
    personagem = "Assistente"
    message = f"Voce é um jogador do Jogo Bang Dice Game, seu personagem é o {personagem}, voce acabou de rolar os dados e tirou 3 tiros de 1 distancia, em um dos seu lados está o Xerife e no outro lado um personagem que ainda não jogou, responda apenas dizendo em quem vai ser o tiro e o total de tiros"
    data = chat_controller.add_message(new_message=message, chat_id=chat_id)
    return ResponseDTO(data=data)


@chat_ai_router.post(
    "/teste",
    responses={201: {"model": ResponseModelDTO[ChatDTO]}},
    response_model=ResponseModelDTO[ChatDTO],
)
async def teste(chat_id: str | None = None):
    chat_controller = ChatController()
    personagem = "Assistente"
    # message = f"Voçê acabou de rolar os dados e tirou 3 tiros de 1 distancia, em um dos seu lados está o Xerife e no outro lado o Aragão que ainda não jogou, responda apenas dizendo em quem vai ser o tiro e o total de tiros"
    # data = chat_controller.run_setup(personagem=personagem)
    message = chat_controller.run_bollets(user_name="Lucas", personagem=personagem)
    data = chat_controller.add_message(new_message=message, chat_id=chat_id)
    return ResponseDTO(data=data)
