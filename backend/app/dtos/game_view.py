from typing import Any, Optional

from pydantic import Field

from app.dtos.base import BaseDTO
from app.dtos.character import IdentityDTO, TeamDTO


class MeViewDTO(BaseDTO):
    user_id: int
    identity: IdentityDTO


class PlayerViewDTO(BaseDTO):
    user_id: int
    user_name: str
    seat: int
    character: str = Field(default="")
    life: int
    max_life: int
    arrows: int
    is_alive: bool
    is_bot: bool
    public_identity: Optional[IdentityDTO] = Field(default=None)
    distance_from_me: Optional[int] = Field(default=None)


class DieViewDTO(BaseDTO):
    index: int
    face: Optional[str] = Field(default=None)
    locked: bool = Field(default=False)
    can_reroll: bool = Field(default=False)
    resolved: bool = Field(default=False)
    valid_target_user_ids: list[int] = Field(default_factory=list)


class EventViewDTO(BaseDTO):
    id: int
    type: str
    round_number: int
    turn_number: int
    actor_user_id: Optional[int] = Field(default=None)
    target_user_id: Optional[int] = Field(default=None)
    amount: int = Field(default=0)
    actor_public_identity: Optional[IdentityDTO] = Field(default=None)
    target_public_identity: Optional[IdentityDTO] = Field(default=None)
    data: dict[str, Any] = Field(default_factory=dict)


class GameViewDTO(BaseDTO):
    game_id: str
    version: int
    status: str
    phase: str
    round_number: int
    turn_number: int
    current_user_id: int
    rolls_left: int
    arrows_in_pile: int
    me: MeViewDTO
    players: list[PlayerViewDTO] = Field(default_factory=list)
    dice: list[DieViewDTO] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)
    winner: Optional[TeamDTO] = Field(default=None)
    events: list[EventViewDTO] = Field(default_factory=list)
    last_event_id: int = Field(default=0)


# ---------- comandos ----------


class CommandDTO(BaseDTO):
    actor_user_id: int
    expected_version: int


class RollCommandDTO(CommandDTO):
    reroll_indexes: list[int] = Field(default_factory=list)


class StopRollingCommandDTO(CommandDTO):
    pass


class DiceAssignmentDTO(BaseDTO):
    dice_index: int
    target_user_id: int


class ResolveCommandDTO(CommandDTO):
    assignments: list[DiceAssignmentDTO] = Field(default_factory=list)


class FinishTurnV2CommandDTO(CommandDTO):
    pass


class AdvanceBotsCommandDTO(BaseDTO):
    expected_version: int
    since_event_id: Optional[int] = Field(default=None)
