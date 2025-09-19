from typing import Optional
from pydantic import Field

from app.dtos.base import DTO, BaseDTO
from app.dtos.character import CharacterDTO
from app.dtos.session import SessionDTO


class PlayerDTO(BaseDTO):
    user_id: int = Field(default=0)
    user_name: str = Field(default="")
    # disabled: bool = Field(default=False)
    position: int = Field(default=0)
    # admin: bool = Field(default=False)
    # admin_master: bool = Field(default=False)
    # session: list[SessionDTO] = Field(...)
    is_alive: bool = Field(default=True)
    is_bot: bool = Field(default=True)
    arrow: int = Field(default=0)
    bullet: int = Field(default=0)

    character: Optional[CharacterDTO] = Field(default=None)
    # identity: Identity

    # team: Team
