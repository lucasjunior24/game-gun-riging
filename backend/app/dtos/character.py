from pydantic import Field

from app.dtos.base import DTO
from app.dtos.session import SessionDTO


class PlayerDTO(DTO):
    user_id: str = Field(default="")
    user_name: str = Field(default="")
    hashed_password: str = Field(default="")
    disabled: bool = Field(default=False)
    position: int = Field(default=0)
    admin: bool = Field(default=False)
    admin_master: bool = Field(default=False)
    session: list[SessionDTO] = Field(...)
    is_alive: bool = Field(default=True)
    is_bot: bool = Field(default=True)
    arrow: int = Field(default=0)
    bullet: int = Field(default=0)

    character: Character | undefined
    identity: Identity

    team: Team
