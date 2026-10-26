import random

from app.bot.agent import BayesAgent
from app.engine.rules import GameEngine
from app.engine.state import GameStatus
from app.services.bot_turn_runner import BotTurnRunner

from conftest import make_specs


def test_full_game_between_bots_always_ends_with_a_winner():
    engine = GameEngine()

    for seed in range(50):
        state = engine.new_game(
            "g", make_specs(5, all_bots=True), random.Random(seed), shuffle_roles=False
        )
        # Poucas amostras: aqui so importa que toda decisao seja valida e a partida acabe
        runner = BotTurnRunner(engine, BayesAgent(engine, seed=seed, n_samples=8))
        for _ in range(500):
            if state.status is GameStatus.DONE:
                break
            state = runner.play_turn(state)
        assert state.status is GameStatus.DONE, f"seed {seed} nao terminou"
        assert state.winner is not None
