from dataclasses import dataclass
from enum import Enum


class DiceFace(Enum):
    SHOT_1 = "1"
    SHOT_2 = "2"
    DYNAMITE = "Dinamite"
    BEER = "Cerveja"
    ARROW = "Flecha"
    GATLING = "Metralhadora"


FACES = tuple(DiceFace)
DICE_COUNT = 5
MAX_ROLLS = 3
DYNAMITE_LIMIT = 3
GATLING_MIN = 3


@dataclass
class Die:
    index: int
    face: DiceFace | None = None
    locked: bool = False
    resolved: bool = False

    @property
    def can_reroll(self) -> bool:
        return self.face is not DiceFace.DYNAMITE
