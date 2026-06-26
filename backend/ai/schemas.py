from pydantic import BaseModel
from typing import List, Dict


class Player(BaseModel):
    id: int
    vida: int
    distancia: int
    suspeita: float
    papel_estimado: str


class Event(BaseModel):
    attacker_id: int
    target_id: int
    action: str  # "tiro", "gatling", etc.


class GameState(BaseModel):
    vida: int
    vida_max: int
    personagem: str
    papel: str

    self_id: int

    dados: List[str]
    rerolls_restantes: int

    players: List[Player]

    history: List[Event]  # 🔥 memória do jogo
