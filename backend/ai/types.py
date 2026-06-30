from typing import List, Literal, TypedDict

Role = Literal["xerife", "fora_da_lei", "renegado", "vice"]
ActionType = Literal["tiro", "gatling", "cerveja"]


class PlayerState(TypedDict):
    id: int
    vida: int
    distancia: int
    suspeita: float
    papel_prob: dict[Role, float]  # 🔥 Bayes


class Event(TypedDict):
    attacker_id: int
    target_id: int
    action: ActionType


class GameState(TypedDict):
    self_id: int
    vida: int
    vida_max: int
    papel: Role
    personagem: str

    dados: List[str]
    rerolls_restantes: int

    players: List[PlayerState]
    history: List[Event]
