from typing import Optional
import torch

from ai.types import GameState
from ai.predictor import BehaviorPredictor


class MLPolicy:

    def __init__(self, predictor: BehaviorPredictor) -> None:
        self.predictor = predictor

    def choose_target(self, state: GameState) -> Optional[int]:

        probs: torch.Tensor = self.predictor.predict_target_probs(state)

        best_target: int = int(torch.argmax(probs).item())

        return best_target

    def decide(self, state: GameState) -> str:
        dados = state["dados"]
        if "tiro" in dados:
            target = self.choose_target(state)
            if target is not None:
                return f"atacar_{target}"

        return "passar"
