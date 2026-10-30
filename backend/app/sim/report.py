"""Relatorio de um arquivo de partidas gravado por app.sim.run.

    python -m app.sim.report results/bayes_5p.jsonl
    python -m app.sim.report results/bayes_5p.jsonl --csv results/bayes_5p.csv
"""

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from app.sim.runner import GameResult
from app.sim.stats import (
    belief_logloss,
    death_causes,
    durations,
    friendly_fire,
    seat_rates,
    team_rates,
)


def load_results(path: str | Path) -> list[GameResult]:
    with open(path, encoding="utf-8") as f:
        return [GameResult.from_dict(json.loads(line)) for line in f if line.strip()]


def render(results: list[GameResult]) -> str:
    lines: list[str] = []
    by_players: dict[int, list[GameResult]] = defaultdict(list)
    for r in results:
        by_players[r.players].append(r)
    for players in sorted(by_players):
        lines += _section(players, by_players[players])
    return "\n".join(lines)


def _section(players: int, results: list[GameResult]) -> list[str]:
    timed_out = sum(r.timed_out for r in results)
    lines = [
        f"=== {players} jogadores: {len(results)} partidas ===",
        f"bateram max_turns: {timed_out} ({timed_out / len(results):.1%})"
        + ("  <- deveria ser 0" if timed_out else ""),
        "",
        "Vitoria por time (IC de Wilson 95%):",
    ]
    for team, rate in team_rates(results).items():
        lines.append(f"  {team.value:<12} {rate}")

    agents = {name for r in results for name in r.agent_names}
    if len(agents) > 1:
        lines += ["", "Vitoria por agente (por assento):"]
        for name, rate in seat_rates(results, lambda r, s: r.agent_names[s]).items():
            lines.append(f"  {name:<30} {rate}")
    lines += ["", "Vitoria por agente e papel:"]
    by_role = seat_rates(results, lambda r, s: (r.agent_names[s], r.roles[s].value))
    for (name, role), rate in by_role.items():
        lines.append(f"  {name:<30} {role:<12} {rate}")

    d = durations(results)
    lines += [
        "",
        f"Duracao (turnos): media {d['media']:.1f}, mediana {d['mediana']:.0f}, "
        f"p90 {d['p90']}, rodadas em media {d['rodadas']:.1f}",
    ]

    causes = death_causes(results)
    total = sum(causes.values())
    lines += ["", f"Causas de morte ({total} mortes):"]
    for cause, count in causes.most_common():
        lines.append(f"  {str(cause):<10} {count / total:6.1%}  ({count})")

    lines += ["", "Fogo amigo (tiros em aliado real / tiros):"]
    for name, rate in friendly_fire(results).items():
        lines.append(f"  {name:<30} {rate}")

    loss = belief_logloss(results)
    if loss is not None:
        lines += [
            "",
            f"Log-loss da crenca: {loss:.3f} (chute uniforme entre 3 papeis = {math.log(3):.3f}; "
            "menor e melhor)",
        ]
    lines.append("")
    return lines


def write_csv(results: list[GameResult], path: str | Path) -> None:
    """Uma linha por assento: facil de abrir numa planilha ou no pandas."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["seed", "players", "seat", "agent", "role", "won", "turns", "timed_out", "winner"]
        )
        for r in results:
            for seat in range(r.players):
                writer.writerow(
                    [
                        r.seed,
                        r.players,
                        seat,
                        r.agent_names[seat],
                        r.roles[seat].value,
                        int(r.won(seat)),
                        r.turns,
                        int(r.timed_out),
                        r.winner.value if r.winner else "",
                    ]
                )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--csv")
    args = parser.parse_args(argv)

    results = [r for path in args.files for r in load_results(path)]
    print(render(results))
    if args.csv:
        write_csv(results, args.csv)


if __name__ == "__main__":
    main()
