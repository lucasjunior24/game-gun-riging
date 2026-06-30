from typing import List
import torch
from ai.types import GameState


def encode_sequence(states: List[GameState]) -> torch.Tensor:
    seq: List[List[float]] = []

    for state in states:
        features: List[float] = []

        features.append(state["vida"] / state["vida_max"])

        for p in state["players"]:
            features.extend([p["vida"] / 10.0, p["distancia"] / 5.0, p["suspeita"]])

        seq.append(features)

    return torch.tensor([seq], dtype=torch.float32)  # (1, seq, features)
