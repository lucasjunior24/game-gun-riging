from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from app.dtos.base import DTO
from app.dtos.session import SessionDTO


class GameStatusDTO(Enum):
    idle = "Idle"
    running = "Done"
    done = "Done"
    failed = "Failed"


class MatchGameDTO(DTO):
    status: GameStatusDTO = Field(default=GameStatusDTO.idle)
    players_total: int = Field(default=5)
    champion: Optional[str] = Field(default=None)
    player_name: str


class CreateGameDTO(BaseModel):
    player_name: str
