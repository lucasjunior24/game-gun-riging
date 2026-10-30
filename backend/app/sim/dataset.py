"""Self-play: grava posicoes e o resultado final para treinar a rede de valor.

    python -m app.sim.dataset --games 2000 --players 4,5,6,7,8 --agent bayes:medio:n=10 --out results/data/gen1.npz

Cada linha e (atributos da posicao vista por um jogador, 1 se o time dele venceu).
Os atributos usam so a observacao e a crenca dele, nunca o estado real.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from app.bot.belief import Belief, infer
from app.bot.likelihood import LikelihoodModel, SoftmaxLikelihood
from app.dtos.character import IdentityDTO
from app.engine.state import ARROWS_TOTAL, EngineState
from app.engine.view import PlayerObservation, build_observation
from app.sim.run import parallel_map, with_progress
from app.sim.runner import MAX_TURNS, GameResult, build_agents, play_game

ROLE_ORDER = (
    IdentityDTO.XERIFE,
    IdentityDTO.ASSISTENTE,
    IdentityDTO.FORA_DA_LEI,
    IdentityDTO.RENEGADO,
)
MAX_SEATS = 8
SEAT_FEATURES = 10  # presente, vivo, vida, flechas, Xerife, distancia, 4 probabilidades de papel
GLOBAL_FEATURES = 5
N_FEATURES = len(ROLE_ORDER) + GLOBAL_FEATURES + MAX_SEATS * SEAT_FEATURES
MAX_ROUNDS = 30  # so para normalizar; partidas mais longas ficam em 1

Marginals = dict[int, dict[IdentityDTO, float]]


def marginals_of(belief: Belief, obs: PlayerObservation) -> Marginals:
    """P(papel) de cada jogador oculto. Calcula uma vez por decisao, nao por estado avaliado."""
    return {
        p.seat: belief.marginal(p.seat)
        for p in obs.players
        if p.seat != obs.viewer_seat and p.public_identity is None
    }


def featurize(obs: PlayerObservation, marginals: Marginals) -> np.ndarray:
    """Posicao vista por `obs.viewer_seat`, com ~90 numeros entre 0 e 1.

    Os assentos vem em ordem relativa a mim (eu, o proximo no sentido do turno, ...):
    o modelo nao depende do numero absoluto do assento. Assentos que nao existem
    (menos de 8 jogadores) ficam zerados, com "presente" = 0.
    """
    total = len(obs.players)
    me = obs.viewer_seat
    alive = sum(p.is_alive for p in obs.players)
    x = np.zeros(N_FEATURES, dtype=np.float32)

    x[ROLE_ORDER.index(obs.my_identity)] = 1.0
    g = len(ROLE_ORDER)
    x[g] = obs.arrows_in_pile / ARROWS_TOTAL
    x[g + 1] = alive / total
    x[g + 2] = min(obs.round_number, MAX_ROUNDS) / MAX_ROUNDS
    x[g + 3] = (total - 4) / (MAX_SEATS - 4)
    x[g + 4] = ((obs.current_seat - me) % total) / MAX_SEATS  # de quem e a vez, relativo a mim

    base = g + GLOBAL_FEATURES
    for k in range(total):
        p = obs.players[(me + k) % total]
        f = base + k * SEAT_FEATURES
        x[f] = 1.0
        x[f + 1] = float(p.is_alive)
        x[f + 2] = p.life / p.max_life
        x[f + 3] = p.arrows / ARROWS_TOTAL
        x[f + 4] = float(p.public_identity is IdentityDTO.XERIFE)
        x[f + 5] = (p.distance_from_viewer or 0) / (MAX_SEATS // 2)
        known = obs.my_identity if p.seat == me else p.public_identity
        probs = {known: 1.0} if known is not None else marginals.get(p.seat, {})
        for i, role in enumerate(ROLE_ORDER):
            x[f + 6 + i] = probs.get(role, 0.0)
    return x


def record_game(
    seed: int,
    players: int,
    specs: list[str],
    max_turns: int = MAX_TURNS,
    model: LikelihoodModel | None = None,
) -> tuple[list[dict], GameResult]:
    """Joga uma partida e grava, no inicio de cada turno, a posicao vista por cada vivo.

    Gravar todos os vivos (e nao so quem joga) cobre tambem as posicoes "depois da minha
    jogada, na vez de outro", que sao as que o agente avalia na busca.
    """
    model = model or SoftmaxLikelihood()
    rows: list[dict] = []

    def on_turn(state: EngineState) -> None:
        for p in state.alive_players():
            obs = build_observation(state, p.seat)
            belief = infer(obs, model)
            rows.append(
                {"game": seed, "seat": p.seat, "features": featurize(obs, marginals_of(belief, obs))}
            )

    result = play_game(seed, players, build_agents(specs, seed), max_turns, on_turn=on_turn)
    for row in rows:
        row["label"] = 1.0 if result.won(row["seat"]) else 0.0
    return rows, result


def _record_job(job: tuple[int, int, tuple[str, ...], int]) -> tuple[np.ndarray, np.ndarray, int, bool]:
    seed, players, specs, max_turns = job
    rows, result = record_game(seed, players, list(specs), max_turns)
    if not rows:
        return np.zeros((0, N_FEATURES), np.float32), np.zeros(0, np.float32), seed, result.timed_out
    x = np.stack([r["features"] for r in rows])
    y = np.array([r["label"] for r in rows], dtype=np.float32)
    return x, y, seed, result.timed_out


def generate(
    games: int,
    players: list[int],
    agent: str,
    seed_start: int = 0,
    max_turns: int = MAX_TURNS,
    workers: int | None = None,
) -> dict[str, np.ndarray]:
    # Sementes diferentes para cada numero de jogadores: a semente e o grupo do split
    jobs = [
        (seed_start + i * len(players) + j, n, (agent,) * n, max_turns)
        for i in range(games)
        for j, n in enumerate(players)
    ]
    xs, ys, groups, sizes = [], [], [], []
    skipped = 0
    for (job, (x, y, seed, timed_out)) in zip(
        jobs, with_progress(parallel_map(_record_job, jobs, workers), len(jobs))
    ):
        if timed_out:  # sem resultado, sem rotulo
            skipped += 1
            continue
        xs.append(x)
        ys.append(y)
        groups.append(np.full(len(y), seed, dtype=np.int64))
        sizes.append(np.full(len(y), job[1], dtype=np.int8))
    if skipped:
        print(f"  {skipped} partidas sem vencedor ficaram de fora", file=sys.stderr)
    return {
        "X": np.concatenate(xs),
        "y": np.concatenate(ys),
        "groups": np.concatenate(groups),
        "players": np.concatenate(sizes),
    }


def save(data: dict[str, np.ndarray], path: str | Path, meta: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **data, meta=np.array(json.dumps(meta)))


def load(paths: list[str | Path]) -> dict[str, np.ndarray]:
    """Junta varios arquivos (ex.: geracoes anteriores, para nao esquecer)."""
    parts = [np.load(p) for p in paths]
    return {key: np.concatenate([p[key] for p in parts]) for key in ("X", "y", "groups", "players")}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--games", type=int, default=1000, help="partidas por numero de jogadores")
    parser.add_argument("--players", default="4,5,6,7,8")
    parser.add_argument("--agent", default="bayes:medio:n=10")
    parser.add_argument("--seed-start", type=int, default=1_000_000)
    parser.add_argument("--max-turns", type=int, default=MAX_TURNS)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    players = [int(n) for n in args.players.split(",")]
    start = time.time()
    data = generate(args.games, players, args.agent, args.seed_start, args.max_turns, args.workers)
    # Documenta qual agente gerou os dados: a rede so conhece posicoes que ele produz
    meta = {
        "agent": args.agent,
        "games": args.games,
        "players": players,
        "seed_start": args.seed_start,
        "n_features": N_FEATURES,
        "created": time.strftime("%Y-%m-%d %H:%M"),
    }
    save(data, args.out, meta)
    print(
        f"{len(data['y'])} posicoes de {len(np.unique(data['groups']))} partidas "
        f"em {time.time() - start:.0f}s -> {args.out}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
