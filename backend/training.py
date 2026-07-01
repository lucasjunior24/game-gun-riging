import sys
from pathlib import Path
import random
import torch

ROOT_PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_PROJECT))

from app.dtos.dice import ExecuteDicesDTO, ExecuteDistanceDTO
from app.dtos.players import PlayerDTO
from app.services.policy_service import ShotPolicyShotNet, ShotPolicyTargetNet

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "app" / "models" / "shot_policy_model.pt"
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


def generate_synthetic_examples(count: int = 2000):
    examples = []
    random.seed(42)

    for _ in range(count):
        current_player = PlayerDTO(
            user_name="Alice", user_id=1, bullet=random.randint(0, 3)
        )
        current_identity = random.choice(["Xerife", "Fora da lei", "Renegado"])

        players = [
            PlayerDTO(
                user_name=f"Player{index}",
                user_id=index + 2,
                position=index + 1,
                is_alive=True,
                bullet=random.randint(0, 2),
                arrow=random.randint(0, 2),
            )
            for index in range(3)
        ]

        execution = ExecuteDicesDTO(
            game_id="simulated",
            current_player=current_player,
            current_identity=current_identity,
            table_situation="simulado",
            one_distance=ExecuteDistanceDTO(
                bullet_total=random.randint(1, 3), players_options=players
            ),
            two_distance=ExecuteDistanceDTO(
                bullet_total=random.randint(0, 2), players_options=players[:2]
            ),
        )
        print(f"Execution: {execution.model_dump(exclude=["id"], mode="json")}")
        for _, distance in (
            ("1", execution.one_distance),
            ("2", execution.two_distance),
        ):
            if not distance.players_options or distance.bullet_total <= 0:
                continue

            target = max(
                distance.players_options, key=lambda p: (p.is_alive, p.bullet, p.arrow)
            )
            feature_vector = [
                float(distance.bullet_total),
                float(len(distance.players_options)),
                float(target.position),
                1.0 if target.is_alive else 0.0,
                float(target.bullet),
                float(target.arrow),
                1.0 if target.is_bot else 0.0,
                float(execution.current_player.bullet),
                float(execution.current_player.arrow),
                1.0 if execution.current_identity.lower() == "xerife" else 0.0,
                1.0 if execution.current_player.user_name == target.user_name else 0.0,
                1.0 if distance.bullet_total > 1 else 0.0,
            ]

            examples.append(
                {
                    "feature_vector": feature_vector,
                    "target_label": 1,
                    "shot_label": min(3, max(1, distance.bullet_total)),
                }
            )

    return examples


def train_model(examples):
    torch.manual_seed(42)
    features = torch.tensor(
        [e["feature_vector"] for e in examples], dtype=torch.float32
    )
    target_labels = torch.tensor(
        [e["target_label"] for e in examples], dtype=torch.float32
    )
    shot_labels = torch.tensor([e["shot_label"] for e in examples], dtype=torch.long)

    target_model = ShotPolicyTargetNet(features.shape[1])
    shot_model = ShotPolicyShotNet(features.shape[1])

    target_optimizer = torch.optim.Adam(target_model.parameters(), lr=0.01)
    shot_optimizer = torch.optim.Adam(shot_model.parameters(), lr=0.01)

    for _ in range(20):
        target_optimizer.zero_grad()
        target_logits = target_model(features)
        target_loss = torch.nn.functional.binary_cross_entropy_with_logits(
            target_logits, target_labels
        )
        target_loss.backward()
        target_optimizer.step()

        shot_optimizer.zero_grad()
        shot_logits = shot_model(features)
        shot_loss = torch.nn.functional.cross_entropy(shot_logits, shot_labels - 1)
        shot_loss.backward()
        shot_optimizer.step()

    torch.save(
        {
            "input_size": features.shape[1],
            "target_model_state_dict": target_model.state_dict(),
            "shot_model_state_dict": shot_model.state_dict(),
        },
        MODEL_PATH,
    )


def main():
    print(f"Modelo em {MODEL_PATH}")
    examples = generate_synthetic_examples()
    train_model(examples)
    print(f"Modelo salvo em {MODEL_PATH}")


if __name__ == "__main__":
    main()
