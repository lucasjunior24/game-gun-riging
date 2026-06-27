import torch
from ai.behavior_model import BehaviorModel
from ai.features import encode_state
from ai.types import GameState


class BehaviorPredictor:

    def __init__(self, model: BehaviorModel) -> None:
        self.model: BehaviorModel = model

    def predict_target_probs(self, state: GameState) -> torch.Tensor:

        with torch.no_grad():
            x = encode_state(state)
            logits = self.model(x)
            probs = torch.softmax(logits, dim=0)

        return probs
