import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from app.dtos.character import IdentityDTO
from app.engine.events import EventType, GameEvent

XERIFE = IdentityDTO.XERIFE
ASSISTENTE = IdentityDTO.ASSISTENTE
FORA_DA_LEI = IdentityDTO.FORA_DA_LEI
RENEGADO = IdentityDTO.RENEGADO


class TargetView(Enum):
    """Como o ator enxerga um alvo usando so o que e publico (teoria da mente de nivel 1)."""

    SELF = "self"
    SHERIFF = "sheriff"
    HOSTILE = "hostile"  # ja atirou no Xerife
    FRIENDLY = "friendly"  # ja deu Cerveja ao Xerife
    UNKNOWN = "unknown"


@dataclass
class PublicHistory:
    """Reputacao publica de cada assento, montada evento a evento em ordem."""

    sheriff_seat: int | None
    shot_sheriff: set[int] = field(default_factory=set)
    helped_sheriff: set[int] = field(default_factory=set)

    def view(self, actor_seat: int, target_seat: int) -> TargetView:
        if target_seat == actor_seat:
            return TargetView.SELF
        if target_seat == self.sheriff_seat:
            return TargetView.SHERIFF
        if target_seat in self.shot_sheriff:
            return TargetView.HOSTILE
        if target_seat in self.helped_sheriff:
            return TargetView.FRIENDLY
        return TargetView.UNKNOWN

    def record(self, event: GameEvent) -> None:
        if event.target_seat != self.sheriff_seat or event.actor_seat == self.sheriff_seat:
            return
        if event.type is EventType.SHOT:
            self.shot_sheriff.add(event.actor_seat)
        elif event.type is EventType.BEER:
            self.helped_sheriff.add(event.actor_seat)


class LikelihoodModel(Protocol):
    """P(escolha observada | papel do ator).

    A verossimilhanca depende do mundo so pelo papel de quem agiu: o ator e modelado
    com o que ele ve em publico, e nao com o que ele acredita sobre os outros.
    """

    def is_informative(self, event: GameEvent) -> bool: ...

    def options_at(self, event: GameEvent) -> list[int]: ...

    def likelihood(
        self, event: GameEvent, options: list[int], actor_role: IdentityDTO, history: PublicHistory
    ) -> float: ...


class _ChoiceModel:
    def is_informative(self, event: GameEvent) -> bool:
        # Gatling, ataque indigena e Dinamite atingem todos ou sao sorte: nao houve escolha
        return (
            event.type in (EventType.SHOT, EventType.BEER)
            and event.actor_seat is not None
            and "valid_target_seats" in event.data
        )

    def options_at(self, event: GameEvent) -> list[int]:
        return list(event.data["valid_target_seats"])


# Preferencia w(papel do ator, como ele ve o alvo). Quanto maior, mais ele quer essa jogada.
SHOT_WEIGHTS: dict[IdentityDTO, dict[TargetView, float]] = {
    XERIFE: {TargetView.HOSTILE: 2.0, TargetView.FRIENDLY: -1.0, TargetView.UNKNOWN: 0.0},
    ASSISTENTE: {
        TargetView.SHERIFF: -3.0,
        TargetView.HOSTILE: 2.0,
        TargetView.FRIENDLY: -1.0,
        TargetView.UNKNOWN: 0.0,
    },
    FORA_DA_LEI: {
        TargetView.SHERIFF: 2.0,
        TargetView.HOSTILE: -1.0,
        TargetView.FRIENDLY: 1.0,
        TargetView.UNKNOWN: 0.0,
    },
    RENEGADO: {
        TargetView.SHERIFF: -0.5,
        TargetView.HOSTILE: 0.5,
        TargetView.FRIENDLY: 0.0,
        TargetView.UNKNOWN: 0.0,
    },
}

BEER_WEIGHTS: dict[IdentityDTO, dict[TargetView, float]] = {
    XERIFE: {
        TargetView.SELF: 2.0,
        TargetView.HOSTILE: -2.0,
        TargetView.FRIENDLY: 0.5,
        TargetView.UNKNOWN: -0.5,
    },
    ASSISTENTE: {
        TargetView.SELF: 1.0,
        TargetView.SHERIFF: 2.0,
        TargetView.HOSTILE: -2.0,
        TargetView.FRIENDLY: 0.0,
        TargetView.UNKNOWN: -0.5,
    },
    FORA_DA_LEI: {
        TargetView.SELF: 2.0,
        TargetView.SHERIFF: -3.0,
        TargetView.HOSTILE: 0.5,
        TargetView.FRIENDLY: -1.0,
        TargetView.UNKNOWN: -0.5,
    },
    RENEGADO: {
        TargetView.SELF: 2.0,
        TargetView.SHERIFF: 0.5,
        TargetView.HOSTILE: -1.0,
        TargetView.FRIENDLY: -0.5,
        TargetView.UNKNOWN: -0.5,
    },
}


class SoftmaxLikelihood(_ChoiceModel):
    """O ator escolhe o alvo por softmax_beta(w), misturado com ruido uniforme (mao tremula)."""

    def __init__(self, beta: float = 1.0, epsilon: float = 0.05):
        self.beta = beta
        self.epsilon = epsilon

    def likelihood(
        self, event: GameEvent, options: list[int], actor_role: IdentityDTO, history: PublicHistory
    ) -> float:
        table = (SHOT_WEIGHTS if event.type is EventType.SHOT else BEER_WEIGHTS)[actor_role]
        prefs = [table.get(history.view(event.actor_seat, t), 0.0) for t in options]
        top = max(prefs)
        exps = [math.exp(self.beta * (x - top)) for x in prefs]
        chosen = exps[options.index(event.target_seat)] / sum(exps)
        # Ruido: um comportamento nunca zera um mundo. Zero so vem de restricao dura.
        return (1 - self.epsilon) * chosen + self.epsilon / len(options)


class FixedTable(_ChoiceModel):
    """P(atirar no Xerife | papel) fixa. Serve para reproduzir o exemplo do documento."""

    def __init__(self, shoot_sheriff: dict[IdentityDTO, float]):
        self.shoot_sheriff = shoot_sheriff

    def is_informative(self, event: GameEvent) -> bool:
        return event.type is EventType.SHOT and super().is_informative(event)

    def likelihood(
        self, event: GameEvent, options: list[int], actor_role: IdentityDTO, history: PublicHistory
    ) -> float:
        if actor_role not in self.shoot_sheriff or history.sheriff_seat not in options:
            return 1.0
        p = self.shoot_sheriff[actor_role]
        if event.target_seat == history.sheriff_seat:
            return p
        return (1 - p) / (len(options) - 1)
