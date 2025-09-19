from enum import Enum
from pydantic import Field

from app.dtos.base import DTO, BaseDTO
from app.dtos.session import SessionDTO


class CharacterDTO(BaseDTO):
    user_id: str = Field(default="")

    initial_bullet: int = Field(default=0)
    power: str = Field(default="")
    character: str = Field(default="")
    avatar: str = Field(default="")


class IdentityDTO(Enum):
    XERIFE = "Xerife"
    FORA_DA_LEI = "Fora da lei"
    RENEGADO = "Renegado"
    ASSISTENTE = "Assistente"


class TeamDTO(Enum):
    XERIFE = "Xerife"
    FORA_DA_LEI = "Fora da lei"
    RENEGADO = "Renegado"
