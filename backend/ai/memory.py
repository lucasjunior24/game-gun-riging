import torch
from ai.feature_builder import build_features
from ai.schemas import GameState


def generate_training_data(state: GameState):
    X = []
    y = []

    for event in state.history:
        if event.action != "tiro":
            continue

        for player in state.players:
            features = build_features(state, event.attacker_id, player.id)

            label = 1 if player.id == event.target_id else 0

            X.append(features)
            y.append([label])

    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)
