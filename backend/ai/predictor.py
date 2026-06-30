from typing import List
import torch

from ai.sequence_model import SequenceModel
from ai.behavior_model import BehaviorModel
from ai.features import encode_sequence
from ai.types import GameState


class Predictor:

    def __init__(self, seq_model: SequenceModel, behavior_model: BehaviorModel) -> None:
        self.seq_model = seq_model
        self.behavior_model = behavior_model

    def predict_targets(self, history_states: List[GameState]) -> torch.Tensor:

        seq_tensor: torch.Tensor = encode_sequence(history_states)

        context: torch.Tensor = self.seq_model(seq_tensor)

        logits: torch.Tensor = self.behavior_model(context)

        probs: torch.Tensor = torch.softmax(logits, dim=-1)

        return probs.squeeze(0)
