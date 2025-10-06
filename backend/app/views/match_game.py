from fastapi import APIRouter, Depends

from app.application_manager import ApplicationManager
from app.auth.token import get_token
from app.controllers.game import GameController


from app.controllers.history import HistoryController
from app.dtos.history import HistoryDTO
from app.dtos.match_game import CreateGameDTO, MatchGameDTO
from app.dtos.response import (
    CreateProductDTO,
    ProductModelDTO,
    ResponseDTO,
    ResponseModelDTO,
)

match_game_router = APIRouter(
    prefix="/match_game",
    tags=["Match Game"],
    dependencies=[Depends(get_token)],
    responses={404: {"description": "Not found"}},
)


@match_game_router.get("", response_model=ResponseModelDTO[MatchGameDTO])
async def get_by_id(game_id: str):
    game_controller = ApplicationManager.get(GameController)
    data = game_controller.get_by_id(id=game_id)
    return ResponseDTO(data=data, message="success")


@match_game_router.get("/all", response_model=ResponseModelDTO[list[MatchGameDTO]])
async def get_all():
    game_controller = ApplicationManager.get(GameController)
    data = game_controller.get_all()
    return ResponseDTO(data=data, message="success")


@match_game_router.post("", response_model=ResponseModelDTO[MatchGameDTO])
async def new_match_game(
    game: CreateGameDTO,
):
    game_controller = ApplicationManager.get(GameController)
    game_dto = MatchGameDTO(
        player_name=game.player_name,
        created_by=game.player_name,
        updated_by=game.player_name,
    )
    new_game = game_controller.create(game_dto)

    history_controller = ApplicationManager.get(HistoryController)
    history_dto = HistoryDTO(messages=[], game_id=str(new_game.id))
    history_controller.create(history_dto)

    return ResponseDTO(data=new_game, message="success")


@match_game_router.put("", response_model=ResponseModelDTO[ProductModelDTO])
async def update(
    id: str,
    product: CreateProductDTO,
):

    return ResponseDTO(data=product, message="success")


@match_game_router.delete("", response_model=ResponseModelDTO[ProductModelDTO])
async def delete(product_id: str):
    return ResponseDTO(data=[], message="success")
