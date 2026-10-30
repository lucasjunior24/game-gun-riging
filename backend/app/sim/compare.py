"""Comparacao pareada: trocar o bot de um assento por B melhora o time dele, em relacao a A?

    python -m app.sim.compare --a heuristic --b bayes:medio --games 400 --players 5
    python -m app.sim.compare --a bayes:medio --b bayes:medio:value=app/models/value_net_v1.pt --ref bayes:medio

Para cada semente e cada assento, a mesma partida (mesmos dados, mesmos papeis) e jogada
duas vezes: com A no assento e com B no assento. Os outros assentos usam sempre o agente
de referencia (--ref, por padrao A). Assim a sorte se cancela e o agente testado joga
em todos os papeis. Total de partidas: ate 2 x games x players.
"""

import argparse
from collections import Counter
from dataclasses import dataclass, field

from app.sim.run import parallel_map, run_job, with_progress
from app.sim.runner import MAX_TURNS, GameResult
from app.sim.stats import Rate, mcnemar

ALPHA = 0.05


@dataclass
class Comparison:
    a: str
    b: str
    ref: str
    pairs: int
    a_rate: Rate
    b_rate: Rate
    only_b: int  # sementes em que so B venceu
    only_a: int  # sementes em que so A venceu
    p_value: float
    by_role: dict[str, tuple[Rate, Rate]] = field(default_factory=dict)
    timed_out: int = 0

    @property
    def diff(self) -> float:
        return self.b_rate.p - self.a_rate.p

    @property
    def b_is_better(self) -> bool:
        return self.p_value < ALPHA and self.only_b > self.only_a

    def render(self) -> str:
        lines = [
            f"A = {self.a}",
            f"B = {self.b}",
            f"referencia nos outros assentos = {self.ref}",
            f"{self.pairs} pares (semente x assento)",
            "",
            f"vitoria A: {self.a_rate}",
            f"vitoria B: {self.b_rate}",
            f"diferenca B - A: {self.diff:+.1%}",
            "",
            "Por papel do assento testado:",
        ]
        for role, (ra, rb) in self.by_role.items():
            lines.append(f"  {role:<12} A {ra.p:6.1%}   B {rb.p:6.1%}   ({ra.n} pares)")
        verdict = "B e melhor" if self.b_is_better else (
            "A e melhor" if self.p_value < ALPHA else "sem diferenca significativa"
        )
        lines += [
            "",
            f"pares discordantes: so B venceu {self.only_b}, so A venceu {self.only_a}",
            f"McNemar: p = {self.p_value:.4f} -> {verdict} (alfa = {ALPHA})",
        ]
        if self.timed_out:
            lines.append(f"atencao: {self.timed_out} partidas bateram max_turns (contam como derrota)")
        return "\n".join(lines)


def compare(
    a: str,
    b: str,
    games: int,
    players: int,
    ref: str | None = None,
    seed_start: int = 0,
    max_turns: int = MAX_TURNS,
    workers: int | None = None,
    progress: bool = False,
) -> Comparison:
    ref = ref or a
    seeds = range(seed_start, seed_start + games)

    def lineup(seat: int, agent: str) -> tuple[str, ...]:
        specs = [ref] * players
        specs[seat] = agent
        return tuple(specs)

    # Quando A e a referencia, "A no assento k" e a mesma partida para todo k: roda uma vez so
    keys = {(seed, lineup(seat, agent)) for seed in seeds for seat in range(players) for agent in (a, b)}
    jobs = [(seed, players, specs, max_turns, False) for seed, specs in sorted(keys)]
    results = parallel_map(run_job, jobs, workers)
    if progress:
        results = with_progress(results, len(jobs))
    by_key: dict[tuple, GameResult] = {
        (job[0], job[2]): result for job, result in zip(jobs, results)
    }

    a_wins = b_wins = only_a = only_b = 0
    role_wins: Counter = Counter()
    role_total: Counter = Counter()
    for seed in seeds:
        for seat in range(players):
            ra = by_key[(seed, lineup(seat, a))]
            rb = by_key[(seed, lineup(seat, b))]
            wa, wb = ra.won(seat), rb.won(seat)
            a_wins += wa
            b_wins += wb
            only_a += wa and not wb
            only_b += wb and not wa
            role = ra.roles[seat].value  # mesma semente: mesmo papel nas duas partidas
            role_total[role] += 1
            role_wins[(role, "a")] += wa
            role_wins[(role, "b")] += wb

    pairs = games * players
    _, p_value = mcnemar(only_b, only_a)
    return Comparison(
        a=a,
        b=b,
        ref=ref,
        pairs=pairs,
        a_rate=Rate(a_wins, pairs),
        b_rate=Rate(b_wins, pairs),
        only_b=only_b,
        only_a=only_a,
        p_value=p_value,
        by_role={
            role: (Rate(role_wins[(role, "a")], n), Rate(role_wins[(role, "b")], n))
            for role, n in sorted(role_total.items())
        },
        timed_out=sum(r.timed_out for r in by_key.values()),
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--a", required=True)
    parser.add_argument("--b", required=True)
    parser.add_argument("--ref", help="agente dos outros assentos (padrao: A)")
    parser.add_argument("--games", type=int, default=200, help="sementes; cada uma vira 1 par por assento")
    parser.add_argument("--players", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--max-turns", type=int, default=MAX_TURNS)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args(argv)

    result = compare(
        args.a,
        args.b,
        args.games,
        args.players,
        ref=args.ref,
        seed_start=args.seed_start,
        max_turns=args.max_turns,
        workers=args.workers,
        progress=True,
    )
    print(result.render())


if __name__ == "__main__":
    main()
