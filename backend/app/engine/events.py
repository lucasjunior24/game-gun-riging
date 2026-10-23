from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.dtos.character import IdentityDTO


class EventType(Enum):
    TURN_STARTED = "TURNO_INICIADO"
    DICE_ROLLED = "DADO_ROLADO"
    ARROW_TAKEN = "FLECHA"
    INDIAN_ATTACK = "ATAQUE_INDIGENA"
    DYNAMITE_EXPLODED = "DINAMITE"
    SHOT = "TIRO"
    BEER = "CERVEJA"
    GATLING = "GATLING"
    DAMAGE = "DANO"
    DEATH = "MORTE"
    VICTORY = "VITORIA"


@dataclass
class GameEvent:
    type: EventType
    round_number: int
    turn_number: int
    actor_seat: int | None = None
    target_seat: int | None = None
    amount: int = 0
    # Preenchidos so quando a identidade e publica (Xerife ou morto)
    actor_public_identity: IdentityDTO | None = None
    target_public_identity: IdentityDTO | None = None
    data: dict[str, Any] = field(default_factory=dict)
