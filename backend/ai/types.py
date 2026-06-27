from typing import List, TypedDict, Literal

Role = Literal["xerife", "fora_da_lei", "renegado", "vice"]
Dice = Literal["tiro", "cerveja", "dynamite", "flecha", "gatling"]
ActionType = Literal["tiro", "gatling", "cerveja"]


class PlayerState(TypedDict):
    id: int
    vida: int
    distancia: int
    suspeita: float
    papel_estimado: Role


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

    dados: List[Dice]
    rerolls_restantes: int

    players: List[PlayerState]
    history: List[Event]
