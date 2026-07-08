from typing import Optional
from pydantic import Field

from app.dtos.base import BaseDTO
from app.dtos.character import CharacterDTO, IdentityDTO, TeamDTO
from app.dtos.dice import DiceShowDTO, UserBulletsDTO
from app.dtos.players import IdentityProbabilityDTO


class PublicPlayerDTO(BaseDTO):
    user_id: int = Field(default=0)
    user_name: str = Field(default="")
    position: int = Field(default=0)
    character: Optional[CharacterDTO] = Field(default=None)
    is_alive: bool = Field(default=True)
    is_bot: bool = Field(default=True)
    arrow: int = Field(default=0)
    bullet: int = Field(default=0)
    revealed_identity: Optional[IdentityDTO] = Field(default=None)


class InternalPlayerDTO(PublicPlayerDTO):
    identity: IdentityDTO
    team: TeamDTO
    papel_probability: IdentityProbabilityDTO = Field(
        default_factory=IdentityProbabilityDTO
    )


class GameStateDTO(BaseDTO):
    game_id: str
    status: str = Field(default="Running")
    round_number: int = Field(default=1)
    turn_number: int = Field(default=1)
    current_player: PublicPlayerDTO
    current_player_index: int = Field(default=0)
    players: list[PublicPlayerDTO] = Field(default_factory=list)
    dice: list[DiceShowDTO] = Field(default_factory=list)
    available_actions: list[str] = Field(default_factory=list)
    winner: Optional[TeamDTO] = Field(default=None)


class CreateAuthoritativeGameDTO(BaseDTO):
    player_name: str = Field(default="Lucas")
    players_total: int = Field(default=5)


class ShootDistanceCommandDTO(BaseDTO):
    distance: str
    user_bullets: list[UserBulletsDTO] = Field(default_factory=list)


class ExecuteShotsCommandDTO(BaseDTO):
    actor_user_id: int
    shots_by_distance: list[ShootDistanceCommandDTO] = Field(default_factory=list)


class FinishTurnCommandDTO(BaseDTO):
    actor_user_id: int


class RollDiceCommandDTO(BaseDTO):
    locked_dice_indexes: list[DiceShowDTO] = Field(default_factory=list)


class BotTurnResultDTO(BaseDTO):
    decisions: list[ShootDistanceCommandDTO] = Field(default_factory=list)
