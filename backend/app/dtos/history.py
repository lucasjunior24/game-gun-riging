from enum import Enum
from typing import Optional
from pydantic import Field

from app.dtos.base import DTO, BaseDTO
from app.dtos.character import IdentityDTO
from app.dtos.message import MessageDTO


class ActionTypeDTO(Enum):
    TIRO = "TIRO"
    GATLING = "GATLING"
    CERVEJA = "CERVEJA"
    INDIOS = "INDIOS"


class GameActionHistoryDTO(BaseDTO):
    game_id: str = Field(default="")
    round_number: int = Field(default=0)
    turn_number: int = Field(default=0)
    actor_user_name: str = Field(default="")
    actor_identity: Optional[IdentityDTO] = Field(default=None)
    action_type: ActionTypeDTO = Field(default=ActionTypeDTO.TIRO)
    target_user_name: str = Field(default="")
    target_identity: Optional[IdentityDTO] = Field(default=None)
    distance: Optional[str] = Field(default=None)
    shots: int = Field(default=0)
    target_life_before: Optional[int] = Field(default=None)
    target_life_after: Optional[int] = Field(default=None)
    actor_bullets_before: Optional[int] = Field(default=None)
    actor_bullets_after: Optional[int] = Field(default=None)
    target_arrows_before: Optional[int] = Field(default=None)
    target_arrows_after: Optional[int] = Field(default=None)


class HistoryDTO(DTO):
    messages: list[MessageDTO] = Field(default_factory=list)
    actions: list[GameActionHistoryDTO] = Field(default_factory=list)
    game_id: str
