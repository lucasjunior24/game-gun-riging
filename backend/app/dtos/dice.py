from typing import Optional
from pydantic import BaseModel, Field

from app.dtos.base import BaseDTO
from app.dtos.players import PlayerDTO


class DiceDTO(BaseDTO):
    dice: str = Field(default="")
    locked: bool = Field(default=False)


class DiceShowDTO(BaseDTO):
    dice: int = Field(default=0)
    locked: bool = Field(default=False)
    show: str = Field(default="")


class UserBulletsDTO(BaseDTO):
    user_name: str = Field(default="")
    shoots: int = Field(default=0)


class ShotsDTO(BaseModel):
    user_name: str = Field("Nome de quem vai receber os tiros")
    shoots: int = Field("Quantidade de tiros que você vai dar nesse jogador")


class ExecuteDistanceDTO(BaseDTO):
    bullet_total: int = Field(default=0)
    players_options: list[PlayerDTO] = Field(default_factory=list)
    user_bullets: list[UserBulletsDTO] = Field(default_factory=list)


class ExecuteDicesDTO(BaseDTO):
    current_player: PlayerDTO
    current_identity: str = Field(default="")
    one_distance: ExecuteDistanceDTO
    two_distance: Optional[ExecuteDistanceDTO] = Field(default=None)
