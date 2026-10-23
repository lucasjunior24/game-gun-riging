import random

from app.engine.rules import GameEngine
from app.engine.state import GameStatus
from app.services.bot_turn_runner import BotTurnRunner
from app.services.policy_service import ShotPolicyService

from conftest import make_specs


def test_full_game_between_bots_always_ends_with_a_winner():
    engine = GameEngine()
    policy = ShotPolicyService(model_path="missing-shot-policy-model.pt")

    for seed in range(30):
        state = engine.new_game(
            "g", make_specs(5, all_bots=True), random.Random(seed), shuffle_roles=False
        )
        runner = BotTurnRunner(engine, policy)
        for _ in range(500):
            if state.status is GameStatus.DONE:
                break
            state = runner.play_turn(state)
        assert state.status is GameStatus.DONE, f"seed {seed} nao terminou"
        assert state.winner is not None
