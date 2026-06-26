from fastapi import FastAPI
from ai.schemas import GameState
from ai.agent import BangAgent

app = FastAPI()
agent = BangAgent()


@app.post("/decide")
def decide(state: GameState):
    result = agent.decide(state)
    return result
