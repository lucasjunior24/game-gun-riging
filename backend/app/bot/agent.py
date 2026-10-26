import random
from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar

from app.bot.belief import Belief, infer
from app.bot.determinize import determinize
from app.bot.evaluation import Evaluator, utility_scale
from app.bot.likelihood import LikelihoodModel, SoftmaxLikelihood
from app.bot.reroll import RerollOption, estimate_reroll_values
from app.bot.resolution import Plan, resolution_options
from app.bot.selection import pick
from app.dtos.game_state import DifficultyDTO
from app.engine.dice import DiceFace
from app.engine.rules import Assignment, GameEngine
from app.engine.view import PlayerObservation

A = TypeVar("A")

# Medidas em unidades de rel * saude (1 de dano num inimigo de 8 de vida vale ~0,06):
# diferencas de ~0,01 a 0,2, entao temperaturas pequenas. O agente converte para a escala de V.
TEMPERATURES = {
    DifficultyDTO.DIFICIL: 0.005,
    DifficultyDTO.MEDIO: 0.03,
    DifficultyDTO.FACIL: 0.1,
}
REROLL_SAMPLES = 40

_FACE_LABEL = {DiceFace.SHOT_1: "1", DiceFace.SHOT_2: "2", DiceFace.BEER: "Cerveja"}


@dataclass
class Decision(Generic[A]):
    action: A
    expected_utility: float
    confidence: float  # probabilidade softmax da acao escolhida
    reason: str  # "1 em Murilo (Fora da lei 78%)"
    alternatives: list[tuple[A, float]] = field(default_factory=list)  # top 3, para depuracao


class Agent(Protocol):
    def choose_reroll(self, obs: PlayerObservation) -> Decision[set[int] | None]: ...

    def choose_assignments(self, obs: PlayerObservation) -> Decision[list[Assignment]]: ...


class BayesAgent:
    """Agente sem treino: crenca bayesiana sobre os papeis + utilidade esperada.

    Recebe so a `PlayerObservation`. Nunca le o estado real nem o rng da partida.
    """

    def __init__(
        self,
        engine: GameEngine | None = None,
        difficulty: DifficultyDTO = DifficultyDTO.MEDIO,
        seed: int | None = None,
        model: LikelihoodModel | None = None,
        n_samples: int = REROLL_SAMPLES,
    ):
        self.engine = engine or GameEngine()
        self.difficulty = difficulty
        self.rng = random.Random(seed)
        self.model = model or SoftmaxLikelihood()
        self.n_samples = n_samples

    def choose_reroll(self, obs: PlayerObservation) -> Decision[set[int] | None]:
        belief = infer(obs, self.model)
        evaluator = Evaluator(belief, obs.viewer_seat)
        scores = estimate_reroll_values(
            obs, belief, evaluator.value, self.engine, self.rng, self.n_samples
        )
        choice = pick(scores, self._temperature(obs), self.rng)
        stop_value = scores[0][1]
        return Decision(
            action=set(choice.action) if choice.action is not None else None,
            expected_utility=choice.utility,
            confidence=choice.confidence,
            reason=_reroll_reason(choice.action, choice.utility, stop_value, scores),
            alternatives=[(_as_set(o), u) for o, u in choice.alternatives],
        )

    def choose_assignments(self, obs: PlayerObservation) -> Decision[list[Assignment]]:
        belief = infer(obs, self.model)
        evaluator = Evaluator(belief, obs.viewer_seat)
        # Dano e cura nao dependem dos papeis: simula uma vez, no mundo mais provavel,
        # e so a avaliacao (Evaluator) faz a media sobre todos os mundos.
        state = determinize(obs, belief.most_likely(), random.Random(self.rng.random()))
        temperature = self._temperature(obs)
        options = resolution_options(
            self.engine,
            state,
            obs.viewer_seat,
            evaluator.value,
            chooser=lambda opts: pick(opts, temperature, self.rng).action,
        )
        choice = pick(options, temperature, self.rng)
        return Decision(
            action=choice.action,
            expected_utility=choice.utility,
            confidence=choice.confidence,
            reason=_assignments_reason(choice.action, obs, belief),
            alternatives=choice.alternatives,
        )

    def _temperature(self, obs: PlayerObservation) -> float:
        return TEMPERATURES[self.difficulty] * utility_scale(len(obs.players))


def _as_set(option: RerollOption) -> set[int] | None:
    return set(option) if option is not None else None


def _reroll_reason(
    option: RerollOption, utility: float, stop_value: float, scores: list[tuple[RerollOption, float]]
) -> str:
    if option is None:
        best_roll = max(u for o, u in scores if o is not None) if len(scores) > 1 else None
        if best_roll is None:
            return f"Parou de rolar: valor esperado {utility:.3f}"
        return f"Parou de rolar: valor esperado {utility:.3f}, rolar de novo dava no maximo {best_roll:.3f}"
    dice = ", ".join(str(i + 1) for i in sorted(option))
    return f"Rolou de novo os dados {dice}: valor esperado {utility:.3f} contra {stop_value:.3f} parando"


def _assignments_reason(plan: Plan, obs: PlayerObservation, belief: Belief) -> str:
    if not plan:
        return "Sem dados de 1, 2 ou Cerveja para resolver"
    faces = {d.index: d.face for d in obs.dice}
    parts = []
    for a in plan:
        label = _FACE_LABEL[faces[a.dice_index]]
        if a.target_seat == obs.viewer_seat:
            parts.append(f"{label} em si mesmo")
            continue
        name = obs.players[a.target_seat].user_name
        role, p = max(belief.marginal(a.target_seat).items(), key=lambda item: item[1])
        parts.append(f"{label} em {name} ({role.value} {p:.0%})")
    return "; ".join(parts)
