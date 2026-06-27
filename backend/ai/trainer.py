from typing import List
import torch
import torch.nn as nn
import torch.optim as optim

from ai.behavior_model import BehaviorModel
from ai.features import encode_state
from ai.types import GameState, Event


class BehaviorTrainer:

    def __init__(self, model: BehaviorModel) -> None:
        self.model: BehaviorModel = model
        self.optimizer: optim.Optimizer = optim.Adam(model.parameters(), lr=0.001)
        self.loss_fn: nn.Module = nn.CrossEntropyLoss()

    def train_step(self, states: List[GameState], events: List[Event]) -> float:

        X: List[torch.Tensor] = []
        y: List[int] = []

        for state, event in zip(states, events):

            if event["action"] != "tiro":
                continue

            X.append(encode_state(state))
            y.append(event["target_id"])

        if not X:
            return 0.0

        X_tensor: torch.Tensor = torch.stack(X)
        y_tensor: torch.Tensor = torch.tensor(y, dtype=torch.long)

        logits: torch.Tensor = self.model(X_tensor)

        loss: torch.Tensor = self.loss_fn(logits, y_tensor)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return float(loss.item())
