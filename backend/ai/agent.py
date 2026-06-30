from typing import List

from ai.types import GameState
from ai.sequence_model import SequenceModel
from ai.behavior_model import BehaviorModel
from ai.predictor import Predictor
from ai.policy import AdvancedPolicy


class BangAgent:

    def __init__(self, input_size: int, num_players: int) -> None:

        self.seq_model = SequenceModel(input_size)
        self.behavior_model = BehaviorModel(64, num_players)

        self.predictor = Predictor(self.seq_model, self.behavior_model)
        self.policy = AdvancedPolicy(self.predictor)

        self.history_states: List[GameState] = []

    def update_history(self, state: GameState) -> None:
        self.history_states.append(state)

        if len(self.history_states) > 10:
            self.history_states.pop(0)

    def decide(self, state: GameState) -> str:

        self.update_history(state)

        return self.policy.decide(state, self.history_states)
