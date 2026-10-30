import math
import statistics
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from app.dtos.character import TeamDTO
from app.sim.runner import GameResult

Z_95 = 1.96
EXACT_MCNEMAR_BELOW = 25  # com poucos pares discordantes, o qui-quadrado erra: usa o binomial exato


def wilson(wins: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Intervalo de Wilson para uma proporcao. Melhor que p +- z*sqrt(p(1-p)/n) perto de 0 ou 1."""
    if n == 0:
        return (0.0, 1.0)
    p = wins / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (center - margin, center + margin)


def binomial_two_sided(k: int, n: int) -> float:
    """P-valor bilateral do teste do sinal: k sucessos em n com p = 1/2."""
    if n == 0:
        return 1.0
    k = min(k, n - k)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def mcnemar(b: int, c: int) -> tuple[float, float]:
    """Teste pareado. b = so B venceu, c = so A venceu; os empates nao informam.

    Devolve (estatistica, p-valor). Sem diferenca entre A e B, b e c seguem Binomial(b+c, 1/2).
    """
    n = b + c
    if n == 0:
        return (0.0, 1.0)
    if n < EXACT_MCNEMAR_BELOW:
        return (float(min(b, c)), binomial_two_sided(b, n))
    statistic = (abs(b - c) - 1) ** 2 / n  # com correcao de continuidade
    return (statistic, math.erfc(math.sqrt(statistic / 2)))  # qui-quadrado com 1 grau de liberdade


@dataclass
class Rate:
    wins: int
    n: int

    @property
    def p(self) -> float:
        return self.wins / self.n if self.n else 0.0

    @property
    def ci(self) -> tuple[float, float]:
        return wilson(self.wins, self.n)

    def __str__(self) -> str:
        lo, hi = self.ci
        return f"{self.p:6.1%}  [{lo:5.1%}, {hi:5.1%}]  ({self.wins}/{self.n})"


def team_rates(results: list[GameResult]) -> dict[TeamDTO, Rate]:
    finished = [r for r in results if not r.timed_out]
    return {
        team: Rate(sum(r.winner is team for r in finished), len(finished)) for team in TeamDTO
    }


def seat_rates(results: Iterable[GameResult], key) -> dict:
    """Taxa de vitoria por assento, agrupada por `key(resultado, assento)` (ex.: papel, agente)."""
    wins: Counter = Counter()
    total: Counter = Counter()
    for r in results:
        if r.timed_out:
            continue
        for seat in range(r.players):
            k = key(r, seat)
            total[k] += 1
            wins[k] += r.won(seat)
    return {k: Rate(wins[k], total[k]) for k in sorted(total, key=str)}


def durations(results: list[GameResult]) -> dict[str, float]:
    turns = [r.turns for r in results]
    if not turns:
        return {}
    ordered = sorted(turns)
    return {
        "media": statistics.fmean(turns),
        "mediana": statistics.median(turns),
        "p90": ordered[min(len(ordered) - 1, int(0.9 * len(ordered)))],
        "rodadas": statistics.fmean(r.rounds for r in results),
    }


def death_causes(results: list[GameResult]) -> Counter:
    return Counter(cause for r in results for _, cause in r.deaths)


def friendly_fire(results: list[GameResult]) -> dict[str, Rate]:
    """Tiros em aliado real / tiros dados, por agente."""
    shots: Counter = Counter()
    friendly: Counter = Counter()
    for r in results:
        for seat, name in enumerate(r.agent_names):
            shots[name] += r.shots[seat]
            friendly[name] += r.friendly_shots[seat]
    return {name: Rate(friendly[name], shots[name]) for name in sorted(shots)}


def belief_logloss(results: list[GameResult]) -> float | None:
    count = sum(r.belief_count for r in results)
    return sum(r.belief_loss for r in results) / count if count else None


def auc(scores: list[float], labels: list[float]) -> float:
    """Area sob a curva ROC = P(um positivo ao acaso ter nota maior que um negativo)."""
    pairs = sorted(zip(scores, labels))
    positives = sum(1 for _, y in pairs if y >= 0.5)
    negatives = len(pairs) - positives
    if positives == 0 or negatives == 0:
        return float("nan")
    rank_sum = 0.0
    i = 0
    while i < len(pairs):  # empates recebem o posto medio
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        mean_rank = (i + 1 + j) / 2
        rank_sum += mean_rank * sum(1 for _, y in pairs[i:j] if y >= 0.5)
        i = j
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)
