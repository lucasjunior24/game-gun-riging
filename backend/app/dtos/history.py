from typing import Optional
from pydantic import Field

from app.dtos.base import DTO
from app.dtos.message import MessageDTO


class HistoryDTO(DTO):
    messages: list[MessageDTO] = Field(default_factory=list)
    game_id: str
