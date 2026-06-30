from fastapi import FastAPI
from ai.types import GameState
from ai.agent import BangAgent

app = FastAPI()
agent = BangAgent(input_size=10, num_players=4)


@app.post("/decide")
def decide(state: GameState):
    result = agent.decide(state)
    return result
