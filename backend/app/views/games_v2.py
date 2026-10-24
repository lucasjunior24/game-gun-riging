from collections.abc import Callable
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException

from app.auth.token import get_token
from app.dtos.game_state import GameStateDTO
from app.dtos.game_view import (
    AdvanceBotsCommandDTO,
    FinishTurnV2CommandDTO,
    GameViewDTO,
    ResolveCommandDTO,
    RollCommandDTO,
    StopRollingCommandDTO,
)
from app.dtos.response import ResponseDTO, ResponseModelDTO
from app.engine.errors import RuleViolation
from app.services.game_errors import GameNotFound, NotYourTurn, StaleVersion
from app.views.game_state import game_service

# Rotas autoritativas (Fase 2). Ficam num arquivo separado para facilitar
# apagar as rotas antigas de game_state.py na Fase 6.
games_v2_router = APIRouter(
    prefix="/games",
    tags=["Games"],
    dependencies=[Depends(get_token)],
    responses={
        400: {"description": "Acao contra a regra"},
        403: {"description": "Nao e a vez de quem pediu"},
        404: {"description": "Partida nao encontrada"},
        409: {"description": "Versao desatualizada"},
    },
)

ViewResponse = ResponseModelDTO[GameViewDTO]


def _run[T](action: Callable[[], T]) -> ResponseDTO[T]:
    """Traduz os erros de cada camada (servico e motor) para o HTTP certo."""
    try:
        data = action()
    except GameNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotYourTurn as error:
        raise HTTPException(status_code=403, detail=str(error))
    except StaleVersion as error:
        raise HTTPException(status_code=409, detail=str(error))
    except (RuleViolation, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error))
    return ResponseDTO(data=data, message="success")


@games_v2_router.get(
    "/{game_id}/state",
    response_model=ResponseModelDTO[Union[GameViewDTO, GameStateDTO]],
)
async def get_game_state(
    game_id: str,
    viewer_user_id: Optional[int] = None,
    since_event_id: Optional[int] = None,
):
    """Com `viewer_user_id`, devolve a visao daquele jogador (GameViewDTO).

    Sem ele, devolve o formato antigo (GameStateDTO) ate o front migrar na Fase 3.
    """
    if viewer_user_id is None:
        return _run(lambda: game_service.get_state(game_id))
    return _run(lambda: game_service.get_view(game_id, viewer_user_id, since_event_id))


@games_v2_router.post("/{game_id}/roll", response_model=ViewResponse)
async def roll(game_id: str, command: RollCommandDTO):
    return _run(lambda: game_service.roll(game_id, command))


@games_v2_router.post("/{game_id}/stop-rolling", response_model=ViewResponse)
async def stop_rolling(game_id: str, command: StopRollingCommandDTO):
    return _run(lambda: game_service.stop_rolling(game_id, command))


@games_v2_router.post("/{game_id}/resolve", response_model=ViewResponse)
async def resolve(game_id: str, command: ResolveCommandDTO):
    return _run(lambda: game_service.resolve(game_id, command))


@games_v2_router.post("/{game_id}/finish-turn", response_model=ViewResponse)
async def finish_turn(game_id: str, command: FinishTurnV2CommandDTO):
    return _run(lambda: game_service.finish_turn(game_id, command))


@games_v2_router.post("/{game_id}/bots/advance", response_model=ViewResponse)
async def advance_bots(game_id: str, command: AdvanceBotsCommandDTO):
    return _run(lambda: game_service.advance_bots(game_id, command))
