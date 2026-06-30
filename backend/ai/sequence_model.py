from typing import List
import torch
import torch.nn as nn


class SequenceModel(nn.Module):

    def __init__(self, input_size: int, hidden_size: int = 64) -> None:
        super().__init__()

        self.lstm: nn.LSTM = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc: nn.Linear = nn.Linear(hidden_size, hidden_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_size)
        out, _ = self.lstm(x)
        last: torch.Tensor = out[:, -1, :]
        return self.fc(last)
