"""Roda N partidas bot contra bot em paralelo e grava uma linha JSON por partida.

    python -m app.sim.run --games 2000 --players 5 --agent bayes:medio --out results/bayes_5p.jsonl
    python -m app.sim.run --games 500 --players 4,5,8 --agent heuristic --out results/heur.jsonl
    python -m app.sim.run --games 200 --players 5 --seats heuristic,bayes,bayes,bayes,bayes ...
"""

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import TypeVar

from app.sim.runner import MAX_TURNS, GameResult, build_agents, play_game

J = TypeVar("J")
R = TypeVar("R")

GameJob = tuple[int, int, tuple[str, ...], int, bool]  # semente, jogadores, agentes, max_turns, crenca


def run_job(job: GameJob) -> GameResult:
    seed, players, specs, max_turns, track_belief = job
    model = None
    if track_belief:
        from app.bot.likelihood import SoftmaxLikelihood

        model = SoftmaxLikelihood()
    return play_game(seed, players, build_agents(list(specs), seed), max_turns, model)


def parallel_map(fn: Callable[[J], R], jobs: list[J], workers: int | None = None) -> Iterator[R]:
    """Cada partida e independente (problema embaracosamente paralelo): um processo por nucleo.

    Devolve na ordem dos jobs, para o resultado nao depender do agendamento.
    """
    workers = workers or os.cpu_count() or 1
    if workers <= 1 or len(jobs) <= 1:
        yield from map(fn, jobs)
        return
    chunk = max(1, len(jobs) // (workers * 8))
    with mp.get_context("spawn").Pool(workers) as pool:
        yield from pool.imap(fn, jobs, chunksize=chunk)


def with_progress(items: Iterable[R], total: int, every: int = 100) -> Iterator[R]:
    start = time.time()
    for i, item in enumerate(items, 1):
        if i % every == 0 or i == total:
            rate = i / max(time.time() - start, 1e-9)
            print(f"  {i}/{total} partidas ({rate:.1f}/s)", file=sys.stderr, flush=True)
        yield item


def game_jobs(
    games: int,
    players: list[int],
    seats: list[str] | None,
    agent: str,
    seed_start: int,
    max_turns: int,
    track_belief: bool,
) -> list[GameJob]:
    jobs = []
    for n in players:
        specs = tuple(seats) if seats else (agent,) * n
        if len(specs) != n:
            raise SystemExit(f"--seats tem {len(specs)} agentes para {n} jogadores")
        jobs += [
            (seed, n, specs, max_turns, track_belief)
            for seed in range(seed_start, seed_start + games)
        ]
    return jobs


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--games", type=int, default=1000, help="partidas por numero de jogadores")
    parser.add_argument("--players", default="5", help="ex.: 5 ou 4,5,8")
    parser.add_argument("--agent", default="bayes:medio", help="agente de todos os assentos")
    parser.add_argument("--seats", help="um agente por assento, separados por virgula")
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--max-turns", type=int, default=MAX_TURNS)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--belief", action="store_true", help="mede o log-loss da crenca")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    players = [int(n) for n in args.players.split(",")]
    seats = args.seats.split(",") if args.seats else None
    jobs = game_jobs(
        args.games, players, seats, args.agent, args.seed_start, args.max_turns, args.belief
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for result in with_progress(parallel_map(run_job, jobs, args.workers), len(jobs)):
            f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")
    print(f"{len(jobs)} partidas gravadas em {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
