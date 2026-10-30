from functools import lru_cache
from pathlib import Path

import numpy as np

from app.bot.belief import Belief
from app.bot.evaluation import Evaluator
from app.engine.state import EngineState
from app.engine.view import PlayerObservation, build_observation
from app.sim.dataset import featurize, marginals_of


class NumpyValueNet:
    """Os pesos da `ValueNet` treinada, rodando em numpy.

    A busca avalia milhares de estados por decisao, um de cada vez: com uma rede tao pequena,
    o custo de chamar o torch para cada um e maior que a conta em si.
    """

    def __init__(self, layers: list[tuple[np.ndarray, np.ndarray]]):
        self.layers = layers

    @classmethod
    def load(cls, path: str | Path) -> "NumpyValueNet":
        from app.sim.train_value import load_model

        model = load_model(path)
        linears = [m for m in model.net if hasattr(m, "weight")]
        return cls(
            [(m.weight.detach().numpy().T.copy(), m.bias.detach().numpy().copy()) for m in linears]
        )

    def logit(self, x: np.ndarray) -> float:
        for i, (w, b) in enumerate(self.layers):
            x = x @ w + b
            if i < len(self.layers) - 1:
                x = np.maximum(x, 0.0)  # ReLU
        return float(x[0])

    def win_probability(self, x: np.ndarray) -> float:
        return 1.0 / (1.0 + np.exp(-self.logit(x)))


class ValueNetEvaluator:
    """Troca a heuristica escrita a mao pela rede: V = 2 * P(meu time vence) - 1, em [-1, 1].

    Quando a partida acabou num mundo da crenca, o valor exato (+1/-1) continua vindo do
    `Evaluator`: a rede so responde pelos mundos em que o jogo segue.
    """

    def __init__(self, belief: Belief, me: int, obs: PlayerObservation, net: NumpyValueNet):
        self.me = me
        self.net = net
        self.exact = Evaluator(belief, me)
        self.marginals = marginals_of(belief, obs)  # uma vez por decisao, nao por estado
        self._cache: dict[tuple, float] = {}

    def value(self, state: EngineState) -> float:
        terminal, p_ongoing, _ = self.exact.summary(state)
        if p_ongoing == 0:
            return terminal
        key = _signature(state)
        if key not in self._cache:
            x = featurize(build_observation(state, self.me), self.marginals)
            self._cache[key] = 2.0 * self.net.win_probability(x) - 1.0
        return terminal + p_ongoing * self._cache[key]


def _signature(state: EngineState) -> tuple:
    return (
        state.turn.seat,
        state.round_number,
        state.arrows_in_pile,
        # Quem morre na simulacao revela o papel do mundo sorteado: entra na chave
        tuple((p.life, p.arrows, p.public_identity) for p in state.players),
    )


@lru_cache(maxsize=None)
def load_value_net(path: str) -> NumpyValueNet:
    return NumpyValueNet.load(path)


def value_evaluator_factory(path: str):
    """Para o `BayesAgent(evaluator_factory=...)`. A rede e carregada uma vez por processo."""
    net = load_value_net(path)
    return lambda belief, me, obs: ValueNetEvaluator(belief, me, obs, net)
