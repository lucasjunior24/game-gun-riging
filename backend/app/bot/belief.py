import math
import random
from dataclasses import dataclass

from app.bot.likelihood import LikelihoodModel, PublicHistory, SoftmaxLikelihood
from app.bot.worlds import World, enumerate_worlds
from app.dtos.character import IdentityDTO
from app.engine.view import PlayerObservation


@dataclass
class Belief:
    """Distribuicao sobre mundos possiveis, guardada em log para nao dar underflow."""

    worlds: list[World]
    log_w: list[float]

    def probabilities(self) -> list[float]:
        m = max(self.log_w)
        exps = [math.exp(x - m) for x in self.log_w]  # log-sum-exp
        total = sum(exps)
        return [e / total for e in exps]

    def marginal(self, seat: int) -> dict[IdentityDTO, float]:
        out: dict[IdentityDTO, float] = {}
        for world, p in zip(self.worlds, self.probabilities()):
            out[world[seat]] = out.get(world[seat], 0.0) + p
        return out

    def most_likely(self) -> World:
        return self.worlds[max(range(len(self.worlds)), key=self.log_w.__getitem__)]

    def sample(self, rng: random.Random, k: int) -> list[World]:
        return rng.choices(self.worlds, weights=self.probabilities(), k=k)


def infer(obs: PlayerObservation, model: LikelihoodModel | None = None) -> Belief:
    """Recalcula a crenca do zero a partir dos eventos publicos (o bot e funcao pura da observacao)."""
    model = model or SoftmaxLikelihood()
    worlds = enumerate_worlds(obs)
    log_w = [0.0] * len(worlds)  # prior uniforme
    sheriff = next(
        (p.seat for p in obs.players if p.public_identity is IdentityDTO.XERIFE), None
    )
    history = PublicHistory(sheriff_seat=sheriff)
    roles = set(worlds[0].values())

    for event in obs.events:
        # As proprias jogadas tem o mesmo papel em todo mundo: nao ensinam nada
        if model.is_informative(event) and event.actor_seat != obs.viewer_seat:
            options = model.options_at(event)
            if len(options) > 1:  # acao forcada nao ensina nada
                # So o papel do ator importa: calcula uma vez por papel, nao por mundo
                log_l = {
                    role: math.log(model.likelihood(event, options, role, history))
                    for role in roles
                }
                for i, world in enumerate(worlds):
                    log_w[i] += log_l[world[event.actor_seat]]
        history.record(event)
    return Belief(worlds, log_w)
