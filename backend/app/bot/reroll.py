import random
from itertools import combinations

from app.bot.belief import Belief
from app.bot.determinize import determinize
from app.bot.resolution import ValueFn, greedy_plan
from app.engine.dice import DiceFace
from app.engine.rules import GameEngine
from app.engine.state import EngineState, GameStatus, TurnPhase
from app.engine.view import PlayerObservation

RerollOption = frozenset[int] | None  # None = parar de rolar


def reroll_options(obs: PlayerObservation) -> list[RerollOption]:
    """Parar, ou um subconjunto nao vazio dos dados que podem rolar (Dinamite nao rola).

    Rolar de novo o dado 0 ou o dado 1, quando os dois mostram "1", da no mesmo: so o
    multiconjunto de faces rolado importa. Fica um representante de cada.
    """
    faces = {d.index: d.face for d in obs.dice}
    rerollable = [d.index for d in obs.dice if d.face is not DiceFace.DYNAMITE]
    options: list[RerollOption] = [None]
    seen: set[tuple[str, ...]] = set()
    for k in range(1, len(rerollable) + 1):
        for chosen in combinations(rerollable, k):
            key = tuple(sorted(faces[i].value for i in chosen))
            if key not in seen:
                seen.add(key)
                options.append(frozenset(chosen))
    return options


def estimate_reroll_values(
    obs: PlayerObservation,
    belief: Belief,
    value_fn: ValueFn,
    engine: GameEngine,
    rng: random.Random,
    n_samples: int,
) -> list[tuple[RerollOption, float]]:
    """Q(opcao) por Monte Carlo: media de N rolagens simuladas, cada uma resolvida de forma gulosa.

    Usa os mesmos mundos e sementes para todas as opcoes (numeros aleatorios comuns):
    a diferenca entre duas opcoes fica bem menos ruidosa que cada valor isolado.
    """
    seat = obs.viewer_seat
    worlds = belief.sample(rng, n_samples)
    seeds = [rng.random() for _ in range(n_samples)]
    # Muitas rolagens terminam no mesmo estado (mesmas faces, vidas e flechas): resolve uma vez so
    cache: dict[tuple, float] = {}

    def value_after(sim: EngineState) -> float:
        if not _resolving(sim, seat):  # partida acabou, ou morri rolando
            return value_fn(sim)
        key = _signature(sim)
        if key not in cache:
            cache[key] = greedy_plan(engine, sim, seat, value_fn)[1]
        return cache[key]

    scores = []
    for option in reroll_options(obs):
        total = 0.0
        for world, seed in zip(worlds, seeds):
            # Semente do agente, nunca o rng da partida: senao o bot veria as proximas rolagens
            sim = determinize(obs, world, random.Random(seed))
            if option is None:
                engine.stop_rolling(sim, seat)
            else:
                engine.roll(sim, seat, option)  # flechas, ataque indigena e Dinamite acontecem aqui
                if _rolling(sim, seat):
                    engine.stop_rolling(sim, seat)  # politica de rollout: para depois
            total += value_after(sim)
        scores.append((option, total / n_samples))
    return scores


def _rolling(state: EngineState, seat: int) -> bool:
    return _my_phase(state, seat, TurnPhase.ROLLING)


def _resolving(state: EngineState, seat: int) -> bool:
    return _my_phase(state, seat, TurnPhase.RESOLVING)


def _my_phase(state: EngineState, seat: int, phase: TurnPhase) -> bool:
    return state.status is GameStatus.RUNNING and state.turn.seat == seat and state.turn.phase is phase


def _signature(state: EngineState) -> tuple:
    return (
        tuple(sorted(d.face.value for d in state.turn.dice)),
        tuple(p.life for p in state.players),
        tuple(p.arrows for p in state.players),
        state.arrows_in_pile,
    )
