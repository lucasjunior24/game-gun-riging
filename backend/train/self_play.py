from ai.env import BangEnvironment
from ai.agent import BangAgent

env = BangEnvironment()
agent = BangAgent()


def run_episode():
    state = env.reset()
    total_reward = 0

    for _ in range(20):
        action = agent.decide(type("obj", (object,), state))
        state, reward, done = env.step(action)

        total_reward += reward

        if done:
            break

    return total_reward


if __name__ == "__main__":
    for i in range(10):
        print(f"Episode {i}: {run_episode()}")
