"""Ajusta os numeros chutados da Fase 4.

Crenca (beta e epsilon do modelo de verossimilhanca): minimiza o log-loss do papel real.
E maxima verossimilhanca, e nao depende de quem ganhou. Busca em grade.

    python -m app.sim.tune belief --games 300 --players 5 --betas 0.5,1,2,4 --epsilons 0.02,0.05,0.1,0.2

Avaliacao (tabela rel, morte, risco das flechas): maximiza a vitoria. Sem derivada, cada
ponto custa uma comparacao pareada. Busca aleatoria e depois hill climbing (1+1)-ES:
um candidato so substitui o melhor se vencer de forma significativa (McNemar).

    python -m app.sim.tune eval --agent bayes:medio:n=10 --games 100 --players 5 --random 10 --steps 20

Cuidado com o sobreajuste ao adversario: no fim, o melhor e comparado com o padrao em
sementes novas, e tambem contra o heuristico (--check-ref heuristic).
"""

import argparse
import json
import math
import random
import sys
from pathlib import Path

from app.bot.evaluation import DEFAULT_PARAMS, EvalParams
from app.bot.likelihood import SoftmaxLikelihood
from app.engine.state import EngineState
from app.sim.compare import compare
from app.sim.run import parallel_map, with_progress
from app.sim.runner import MAX_TURNS, belief_logloss, build_agents, play_game

# Limites que mantem o sentido de cada parametro (ex.: morrer nunca e bom)
BOUNDS = {"death_score": (-1.0, 0.0), "arrow_risk": (0.0, 1.0)}

BeliefJob = tuple[int, int, tuple[str, ...], int, tuple[tuple[float, float], ...]]


# ---------- crenca ----------


def _belief_job(job: BeliefJob) -> list[tuple[float, int]]:
    """Joga uma partida e mede, a cada turno, o log-loss de cada (beta, epsilon) da grade."""
    seed, players, specs, max_turns, grid = job
    models = [SoftmaxLikelihood(beta=b, epsilon=e) for b, e in grid]
    totals = [[0.0, 0] for _ in grid]

    def on_turn(state: EngineState) -> None:
        for i, model in enumerate(models):
            loss, count = belief_logloss(state, state.turn.seat, model)
            totals[i][0] += loss
            totals[i][1] += count

    play_game(seed, players, build_agents(list(specs), seed), max_turns, on_turn=on_turn)
    return [(loss, count) for loss, count in totals]


def tune_belief(
    games: int,
    players: int,
    agent: str,
    betas: list[float],
    epsilons: list[float],
    seed_start: int = 0,
    workers: int | None = None,
) -> list[tuple[float, float, float]]:
    """Devolve (beta, epsilon, log-loss medio), do melhor para o pior.

    Todos os pontos da grade sao medidos nas mesmas partidas: a comparacao entre eles e justa.
    """
    grid = tuple((b, e) for b in betas for e in epsilons)
    jobs = [
        (seed, players, (agent,) * players, MAX_TURNS, grid)
        for seed in range(seed_start, seed_start + games)
    ]
    sums = [[0.0, 0] for _ in grid]
    for per_game in with_progress(parallel_map(_belief_job, jobs, workers), len(jobs)):
        for i, (loss, count) in enumerate(per_game):
            sums[i][0] += loss
            sums[i][1] += count
    table = [(b, e, s[0] / max(1, s[1])) for (b, e), s in zip(grid, sums)]
    return sorted(table, key=lambda row: row[2])


# ---------- avaliacao ----------


def random_params(rng: random.Random) -> EvalParams:
    """Cada numero vira o padrao vezes U(0,5; 1,5): mantem o sinal, que e a parte que sabemos."""
    return _clamped({k: v * rng.uniform(0.5, 1.5) for k, v in DEFAULT_PARAMS.flat().items()})


def perturb(params: EvalParams, rng: random.Random, sigma: float) -> EvalParams:
    """Passo do (1+1)-ES: multiplica cada numero por exp(N(0, sigma))."""
    return _clamped({k: v * math.exp(rng.gauss(0, sigma)) for k, v in params.flat().items()})


def _clamped(values: dict[str, float]) -> EvalParams:
    for key, (lo, hi) in BOUNDS.items():
        values[key] = min(hi, max(lo, values[key]))
    return EvalParams.from_flat(values)


def _write_params(params: EvalParams, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(params.flat(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path.as_posix()


def tune_eval(
    agent: str,
    games: int,
    players: int,
    random_trials: int,
    steps: int,
    sigma: float,
    out_dir: Path,
    seed: int = 0,
    workers: int | None = None,
) -> tuple[EvalParams, str]:
    rng = random.Random(seed)
    best = DEFAULT_PARAMS
    best_spec = agent  # sem params= e o padrao
    seed_start = 0
    log = (out_dir / "trials.jsonl").open("w", encoding="utf-8")

    trials = ["random"] * random_trials + ["es"] * steps
    for i, kind in enumerate(trials):
        candidate = random_params(rng) if kind == "random" else perturb(best, rng, sigma)
        spec = f"{agent}:params={_write_params(candidate, out_dir / f'trial_{i:03d}.json')}"
        # Sementes novas a cada tentativa: escolher o melhor de muitos nas mesmas sementes
        # premia quem teve sorte nelas
        result = compare(best_spec, spec, games, players, seed_start=seed_start, workers=workers)
        seed_start += games
        promoted = result.b_is_better
        print(
            f"[{i + 1}/{len(trials)}] {kind:<6} B-A {result.diff:+.1%}  p={result.p_value:.3f}"
            + ("  -> novo melhor" if promoted else ""),
            file=sys.stderr,
        )
        log.write(json.dumps({
            "trial": i, "kind": kind, "params": candidate.flat(), "diff": result.diff,
            "p_value": result.p_value, "only_b": result.only_b, "only_a": result.only_a,
            "promoted": promoted,
        }) + "\n")
        log.flush()
        if promoted:
            best, best_spec = candidate, spec
    log.close()
    return best, best_spec


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)

    b = sub.add_parser("belief", help="grade de beta e epsilon pelo log-loss")
    b.add_argument("--games", type=int, default=200)
    b.add_argument("--players", type=int, default=5)
    b.add_argument("--agent", default="bayes:medio:n=10", help="quem joga as partidas medidas")
    b.add_argument("--betas", default="0.25,0.5,1,2,4")
    b.add_argument("--epsilons", default="0.01,0.05,0.1,0.2")
    b.add_argument("--workers", type=int, default=None)

    e = sub.add_parser("eval", help="busca dos parametros da avaliacao pela vitoria")
    e.add_argument("--agent", default="bayes:medio:n=10")
    e.add_argument("--games", type=int, default=100, help="sementes por comparacao")
    e.add_argument("--players", type=int, default=5)
    e.add_argument("--random", type=int, default=10, help="tentativas de busca aleatoria")
    e.add_argument("--steps", type=int, default=20, help="passos de hill climbing")
    e.add_argument("--sigma", type=float, default=0.2)
    e.add_argument("--seed", type=int, default=0)
    e.add_argument("--check-ref", default="heuristic", help="adversario extra da validacao final")
    e.add_argument("--out-dir", default="results/tune")
    e.add_argument("--workers", type=int, default=None)
    args = parser.parse_args(argv)

    if args.mode == "belief":
        table = tune_belief(
            args.games, args.players, args.agent,
            [float(x) for x in args.betas.split(",")],
            [float(x) for x in args.epsilons.split(",")],
            workers=args.workers,
        )
        print(f"{'beta':>6} {'epsilon':>8} {'log-loss':>9}")
        for beta, eps, loss in table:
            print(f"{beta:6.2f} {eps:8.3f} {loss:9.4f}")
        beta, eps, _ = table[0]
        print(f"\nmelhor: beta={beta} epsilon={eps}  (agente: bayes:medio:beta={beta}:eps={eps})")
        return

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    best, best_spec = tune_eval(
        args.agent, args.games, args.players, args.random, args.steps, args.sigma,
        out_dir, args.seed, args.workers,
    )
    best_path = _write_params(best, out_dir / "best.json")
    print(f"\nmelhores parametros em {best_path}")
    if best is DEFAULT_PARAMS:
        print("nenhum candidato venceu o padrao de forma significativa")
        return

    # Validacao em sementes que a busca nunca viu, contra o padrao e contra outro adversario
    fresh = 10_000_000
    print("\n--- validacao: padrao (A) x ajustado (B), sementes novas ---")
    print(compare(args.agent, best_spec, args.games * 2, args.players, seed_start=fresh,
                  workers=args.workers).render())
    print(f"\n--- validacao com {args.check_ref} nos outros assentos ---")
    print(compare(args.agent, best_spec, args.games * 2, args.players, ref=args.check_ref,
                  seed_start=fresh, workers=args.workers).render())


if __name__ == "__main__":
    main()
