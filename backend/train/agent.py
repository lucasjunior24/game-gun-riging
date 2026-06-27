from ai.schemas import GameState
from train.policy import MLPolicy
from ai.predictor import BehaviorPredictor
from ai.behavior_model import BehaviorModel


class BangAgent:

    def __init__(self, num_players: int, input_size: int) -> None:

        self.model = BehaviorModel(input_size, num_players)
        self.predictor = BehaviorPredictor(self.model)
        self.policy = MLPolicy(self.predictor)

    def decide(self, state: GameState):
        return self.policy.decide(state)
