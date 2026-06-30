from typing import Optional, List
import torch

from ai.types import GameState
from ai.predictor import Predictor


class AdvancedPolicy:

    def __init__(self, predictor: Predictor) -> None:
        self.predictor = predictor

    def choose_target(
        self, state: GameState, history_states: List[GameState]
    ) -> Optional[int]:

        probs: torch.Tensor = self.predictor.predict_targets(history_states)

        best: int = int(torch.argmax(probs).item())

        return best

    def decide(self, state: GameState, history_states: List[GameState]) -> str:

        if "tiro" in state["dados"]:
            target: Optional[int] = self.choose_target(state, history_states)
            if target is not None:
                return f"atacar_{target}"

        return "passar"
