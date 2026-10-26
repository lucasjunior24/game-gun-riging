import math
import random
from dataclasses import dataclass
from typing import Generic, TypeVar

A = TypeVar("A")


@dataclass
class Choice(Generic[A]):
    action: A
    utility: float
    confidence: float  # probabilidade softmax da acao escolhida
    alternatives: list[tuple[A, float]]  # top 3 com suas utilidades


def softmax(utilities: list[float], temperature: float) -> list[float]:
    """P(a) = exp(EU(a)/T) / soma exp(EU(b)/T). T = 0 vira argmax (empates dividem)."""
    top = max(utilities)
    if temperature <= 0:
        best = [1.0 if u == top else 0.0 for u in utilities]
        return [b / sum(best) for b in best]
    exps = [math.exp((u - top) / temperature) for u in utilities]
    total = sum(exps)
    return [e / total for e in exps]


def pick(options: list[tuple[A, float]], temperature: float, rng: random.Random) -> Choice[A]:
    """Escolhe uma opcao: a melhor com T baixo, quase ao acaso com T alto."""
    utilities = [u for _, u in options]
    probs = softmax(utilities, temperature)
    if temperature <= 0:
        index = utilities.index(max(utilities))  # empate: a primeira, para ser deterministico
    else:
        index = rng.choices(range(len(options)), weights=probs)[0]
    ranked = sorted(options, key=lambda o: o[1], reverse=True)
    action, utility = options[index]
    return Choice(action, utility, probs[index], ranked[:3])
