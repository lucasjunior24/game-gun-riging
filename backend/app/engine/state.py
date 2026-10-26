import copy
import random
from dataclasses import dataclass, field
from enum import Enum

from app.dtos.character import IdentityDTO, TeamDTO
from app.engine.dice import DICE_COUNT, Die
from app.engine.events import GameEvent

ARROWS_TOTAL = 9


class TurnPhase(Enum):
    ROLLING = "ROLANDO"
    RESOLVING = "RESOLVENDO"


class GameStatus(Enum):
    RUNNING = "Running"
    DONE = "Done"


@dataclass
class EnginePlayer:
    seat: int
    user_id: int
    user_name: str
    identity: IdentityDTO
    max_life: int
    life: int
    is_bot: bool
    character: str = ""
    power: str = ""
    arrows: int = 0
    revealed: bool = False

    @property
    def is_alive(self) -> bool:
        return self.life > 0

    @property
    def public_identity(self) -> IdentityDTO | None:
        if self.identity is IdentityDTO.XERIFE or self.revealed:
            return self.identity
        return None


@dataclass
class TurnState:
    seat: int
    dice: list[Die] = field(default_factory=lambda: [Die(index=i) for i in range(DICE_COUNT)])
    rolls_used: int = 0
    phase: TurnPhase = TurnPhase.ROLLING


@dataclass
class EngineState:
    game_id: str
    players: list[EnginePlayer]
    rng: random.Random
    turn: TurnState
    arrows_in_pile: int = ARROWS_TOTAL
    round_number: int = 1
    turn_number: int = 1
    status: GameStatus = GameStatus.RUNNING
    winner: TeamDTO | None = None
    events: list[GameEvent] = field(default_factory=list)
    # Sobe a cada comando aplicado. Usado no controle de versao otimista da API
    version: int = 0
    next_event_id: int = 1

    @property
    def current_player(self) -> EnginePlayer:
        return self.players[self.turn.seat]

    def alive_players(self) -> list[EnginePlayer]:
        return [p for p in self.players if p.is_alive]

    def clone(self) -> "EngineState":
        """Copia o que muda entre jogadas. Bem mais rapido que deepcopy, e o bot clona muito.

        Eventos sao compartilhados: depois de emitidos, ninguem os altera.
        """
        twin = _shallow(self)
        twin.players = [_shallow(p) for p in self.players]
        twin.rng = _copy_rng(self.rng)
        twin.turn = _shallow(self.turn)
        twin.turn.dice = [_shallow(d) for d in self.turn.dice]
        twin.events = list(self.events)
        return twin


def _shallow(obj):
    # Mesmo efeito de copy.copy num dataclass, sem o custo do protocolo de copia
    twin = object.__new__(type(obj))
    twin.__dict__.update(obj.__dict__)
    return twin


def _copy_rng(rng: random.Random) -> random.Random:
    if type(rng) is not random.Random:
        return copy.deepcopy(rng)  # subclasses (ex.: rng roteirizado dos testes)
    twin = random.Random.__new__(random.Random)  # sem semear: o setstate sobrescreve tudo
    twin.setstate(rng.getstate())  # a tupla de estado e imutavel: nao precisa copiar
    return twin
