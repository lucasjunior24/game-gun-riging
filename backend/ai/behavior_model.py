import torch
import torch.nn as nn


class BehaviorModel(nn.Module):

    def __init__(self, input_size: int, num_players: int) -> None:
        super().__init__()

        self.net: nn.Sequential = nn.Sequential(
            nn.Linear(input_size, 64), nn.ReLU(), nn.Linear(64, num_players)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
