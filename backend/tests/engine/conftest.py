import random

from app.engine.dice import FACES
from app.engine.rules import PlayerSpec


class ScriptedRng(random.Random):
    """Devolve faces pre-definidas em sequencia, ignorando a aleatoriedade real."""

    def __init__(self, faces):
        super().__init__(0)
        self._faces = list(faces)

    def choice(self, seq):
        if seq is FACES:
            return self._faces.pop(0)
        return super().choice(seq)


def make_specs(total: int, all_bots: bool = False, life: int = 4) -> list[PlayerSpec]:
    names = ["Lucas", "Murilo", "Aragao", "Roberto", "Pedro", "Joana", "Clara", "Dudu"]
    return [
        PlayerSpec(
            user_id=index + 1,
            user_name=names[index],
            is_bot=all_bots or index > 0,
            character="Teste",
            life=life,
        )
        for index in range(total)
    ]
