from ai.agent import BangAgent
from ai.types import GameState


def run_demo() -> None:

    agent = BangAgent(input_size=13, num_players=4)

    state: GameState = {
        "self_id": 0,
        "vida": 4,
        "vida_max": 8,
        "papel": "fora_da_lei",
        "personagem": "Suzy",
        "dados": ["tiro", "cerveja", "gatling", "tiro", "tiro"],
        "rerolls_restantes": 0,
        "players": [
            {"id": 0, "vida": 4, "distancia": 0, "suspeita": 0.0, "papel_prob": {}},
            {"id": 1, "vida": 5, "distancia": 1, "suspeita": 0.8, "papel_prob": {}},
            {"id": 2, "vida": 2, "distancia": 2, "suspeita": 0.6, "papel_prob": {}},
            {"id": 3, "vida": 1, "distancia": 1, "suspeita": 0.9, "papel_prob": {}},
        ],
        "history": [],
    }

    action = agent.decide(state)

    print(f"Ação escolhida: {action}")


if __name__ == "__main__":
    run_demo()
