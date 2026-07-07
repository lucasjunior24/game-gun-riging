from fastapi import APIRouter, Depends, HTTPException

from app.auth.token import get_token
from app.dtos.game_state import (
    BotTurnResultDTO,
    CreateAuthoritativeGameDTO,
    ExecuteShotsCommandDTO,
    FinishTurnCommandDTO,
    GameStateDTO,
    RollDiceCommandDTO,
)
from app.dtos.response import ResponseDTO, ResponseModelDTO
from app.services.game_service import GameService

games_router = APIRouter(
    prefix="/games",
    tags=["Games"],
    dependencies=[Depends(get_token)],
    responses={404: {"description": "Not found"}},
)

game_service = GameService()


@games_router.post("", response_model=ResponseModelDTO[GameStateDTO])
async def create_game(command: CreateAuthoritativeGameDTO):
    state = game_service.create_game(command)
    return ResponseDTO(data=state, message="success")


@games_router.get("/{game_id}/state", response_model=ResponseModelDTO[GameStateDTO])
async def get_game_state(game_id: str):
    try:
        state = game_service.get_state(game_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return ResponseDTO(data=state, message="success")


@games_router.post(
    "/{game_id}/actions/shots", response_model=ResponseModelDTO[GameStateDTO]
)
async def execute_shots(game_id: str, command: ExecuteShotsCommandDTO):
    try:
        state = game_service.execute_shots(game_id, command)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return ResponseDTO(data=state, message="success")


@games_router.post(
    "/{game_id}/actions/finish-turn", response_model=ResponseModelDTO[GameStateDTO]
)
async def finish_turn(game_id: str, command: FinishTurnCommandDTO):
    try:
        state = game_service.finish_turn(game_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return ResponseDTO(data=state, message="success")


@games_router.post(
    "/{game_id}/dice/roll", response_model=ResponseModelDTO[GameStateDTO]
)
async def roll_dice(game_id: str, command: RollDiceCommandDTO):
    try:
        state = game_service.roll_dice(game_id, command)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return ResponseDTO(data=state, message="success")


@games_router.post("/{game_id}/bot-turn", response_model=ResponseModelDTO[GameStateDTO])
async def execute_bot_turn(game_id: str):
    try:
        state = game_service.execute_bot_turn(game_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return ResponseDTO(data=state, message="success")
