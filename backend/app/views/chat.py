from app.controllers.chat import ChatController
from fastapi import APIRouter


from app.db.models.product import Product
from app.dtos.dice import DiceShowDTO
from app.dtos.response import (
    CreateProductDTO,
    ProductModelDTO,
    ResponseDTO,
    ResponseModelDTO,
)
from app.services.chat_ai_service import ChatAIService
from app.util.requestsDTOs.chat import ChatDTO
from app.util.schema.product import product_schema

chat_ai_router = APIRouter(
    prefix="/chat_ai",
    tags=["Chat AI"],
    # dependencies=[Depends(get_token)],
    responses={404: {"description": "Not found"}},
)


@chat_ai_router.get("", response_model=ResponseModelDTO[ProductModelDTO])
async def read_system_status(key: str, name: str):
    product = Product.find(key, name)
    dump_data = product_schema.dump(product)
    return ResponseDTO(data=dump_data, message="success")


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
    data = chat_controller.add_message(message=message, chat_id=chat_id)
    return ResponseDTO(data=data)


@chat_ai_router.post(
    "/execute",
    responses={201: {"model": ResponseModelDTO[ChatDTO]}},
    response_model=ResponseModelDTO[ChatDTO],
)
async def execute(personagem: str = "Assistente", chat_id: str | None = None, dices: list[DiceShowDTO]):
    chat_controller = ChatController()
    message = f"Voce é um jogador do Jogo Bang Dice Game, seu personagem é o {personagem}, voce acabou de rolar os dados e tirou 3 tiros de 1 distancia, em um dos seu lados está o Xerife e no outro lado um personagem que ainda não jogou, responda apenas dizendo em quem vai ser o tiro e o total de tiros"
    data = chat_controller.add_message(message=message, chat_id=chat_id)
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
    data = chat_controller.add_message(message=message, chat_id=chat_id)
    return ResponseDTO(data=data)
