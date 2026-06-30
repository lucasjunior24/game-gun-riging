from typing import Dict
from ai.types import PlayerState, Event, Role


def update_beliefs(player: PlayerState, event: Event) -> None:
    probs: Dict[Role, float] = player["papel_prob"]

    if event["attacker_id"] != player["id"]:
        return

    # 🔫 atacou alguém → mais chance de ser fora da lei
    if event["action"] == "tiro":
        probs["fora_da_lei"] *= 1.2
        probs["vice"] *= 0.9

    normalize(probs)


def normalize(probs: Dict[Role, float]) -> None:
    total: float = sum(probs.values())
    for k in probs:
        probs[k] /= total
