import torch
import torch.nn as nn
import torch.optim as optim

from ai.feature_builder import build_features


class OpponentModel(nn.Module):
    def __init__(self, input_size=7):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.net(x)


class OpponentTrainer:
    def __init__(self):
        self.model = OpponentModel()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.loss_fn = nn.BCELoss()

    def train_step(self, features, label):
        pred = self.model(features)
        loss = self.loss_fn(pred, label)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()


def predict_targets(model, state, attacker_id):
    probs = {}

    for player in state.players:
        if player.id == attacker_id:
            continue

        features = build_features(state, attacker_id, player.id)
        features = torch.tensor(features, dtype=torch.float32)

        prob = model(features).item()
        probs[player.id] = prob

    return probs
