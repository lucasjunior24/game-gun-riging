from typing import List
import torch
from ai.types import GameState


def encode_state(state: GameState) -> torch.Tensor:
    features: List[float] = []

    # Self
    features.append(state["vida"] / state["vida_max"])

    # Players
    for p in state["players"]:
        features.extend([p["vida"] / 10.0, p["distancia"] / 5.0, p["suspeita"]])

    return torch.tensor(features, dtype=torch.float32)
