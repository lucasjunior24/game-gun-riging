import random

DADOS = ["tiro", "cerveja", "dynamite", "flecha", "gatling"]


class BangEnvironment:

    def __init__(self):
        self.reset()

    def reset(self):
        self.vida = 8
        return self._get_state()

    def roll_dice(self, n=5):
        return [random.choice(DADOS) for _ in range(n)]

    def step(self, action):
        reward = 0

        if action == "usar_cerveja":
            self.vida += 1
            reward += 0.2

        elif action.startswith("atacar"):
            reward += 0.5

        elif action == "reroll":
            reward -= 0.05

        elif action == "passar":
            reward -= 0.1

        done = self.vida <= 0

        return self._get_state(), reward, done

    def _get_state(self):
        return {
            "vida": self.vida,
            "dados": self.roll_dice(),
            "inimigos_alcance": [1, 2],
            "flechas": random.randint(0, 5),
            "papel_prob": {"xerife": 0.3, "fora_da_lei": 0.7},
        }
