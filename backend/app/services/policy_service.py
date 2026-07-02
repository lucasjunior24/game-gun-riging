from pathlib import Path
import torch

from app.dtos.dice import ExecuteDicesDTO, ExecuteDistanceDTO, UserBulletsDTO
from app.dtos.players import PlayerDTO
from app.dtos.policy import ShotPolicyDecisionDTO, ShotPolicyPredictionDTO


class ShotPolicyTargetNet(torch.nn.Module):
    def __init__(self, input_size: int):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(input_size, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 16),
            torch.nn.ReLU(),
            torch.nn.Linear(16, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


class ShotPolicyShotNet(torch.nn.Module):
    def __init__(self, input_size: int):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(input_size, 24),
            torch.nn.ReLU(),
            torch.nn.Linear(24, 12),
            torch.nn.ReLU(),
            torch.nn.Linear(12, 3),
        )

    def forward(self, x):
        return self.net(x)


class ShotPolicyService:
    def __init__(self, model_path: str = "app/models/shot_policy_model.pt"):
        self.model_path = Path(model_path)
        self.device = torch.device("cpu")
        self.target_model = None
        self.shot_model = None
        self._load_model_if_available()

    def _load_model_if_available(self):
        if not self.model_path.exists():
            return
        checkpoint = torch.load(self.model_path, map_location=self.device)
        self.target_model = ShotPolicyTargetNet(checkpoint["input_size"]).to(
            self.device
        )
        self.shot_model = ShotPolicyShotNet(checkpoint["input_size"]).to(self.device)
        self.target_model.load_state_dict(checkpoint["target_model_state_dict"])
        self.shot_model.load_state_dict(checkpoint["shot_model_state_dict"])
        self.target_model.eval()
        self.shot_model.eval()

    def predict(self, execution: ExecuteDicesDTO) -> ShotPolicyPredictionDTO:
        decisions = []
        for distance_label in ("1", "2"):
            distance = self.get_execution_distance(execution, distance_label)
            if (
                not distance
                or distance.bullet_total <= 0
                or not distance.players_options
            ):
                continue

            if self.target_model is None or self.shot_model is None:
                target_player = max(distance.players_options, key=lambda p: p.position)
                shots = min(3, distance.bullet_total)
                confidence = 0.6
            else:
                target_player = self._predict_target(execution, distance)
                shots = self._predict_shots(execution, distance, target_player)
                confidence = self._predict_confidence(
                    execution, distance, target_player
                )

            decisions.append(
                ShotPolicyDecisionDTO(
                    target_user_name=target_player.user_name,
                    shots=shots,
                    distance=distance_label,
                    confidence=confidence,
                )
            )

        return ShotPolicyPredictionDTO(decisions=decisions)

    def get_execution_distance(
        self, execution: ExecuteDicesDTO, distance_label: str
    ) -> ExecuteDistanceDTO | None:
        distance = (
            execution.one_distance if distance_label == "1" else execution.two_distance
        )

        return distance

    def apply_prediction(
        self, execution: ExecuteDicesDTO, prediction: ShotPolicyPredictionDTO
    ) -> ExecuteDicesDTO:
        for decision in prediction.decisions:
            distance = self.get_distance(execution, decision.distance)
            if distance is None:
                continue
            distance.user_bullets.append(
                UserBulletsDTO(
                    user_name=decision.target_user_name, shots=decision.shots
                )
            )
        return execution

    def _build_feature_vector(
        self,
        execution: ExecuteDicesDTO,
        distance: ExecuteDistanceDTO,
        target_player,
    ):
        features = [
            float(distance.bullet_total),
            float(len(distance.players_options)),
            float(target_player.position),
            1.0 if target_player.is_alive else 0.0,
            float(target_player.bullet),
            float(target_player.arrow),
            1.0 if target_player.is_bot else 0.0,
            float(execution.current_player.bullet),
            float(execution.current_player.arrow),
            1.0 if execution.current_identity.lower() == "xerife" else 0.0,
            (
                1.0
                if execution.current_player.user_name == target_player.user_name
                else 0.0
            ),
            1.0 if distance.bullet_total > 1 else 0.0,
        ]
        return torch.tensor(
            features, dtype=torch.float32, device=self.device
        ).unsqueeze(0)

    def _predict_target(self, execution: ExecuteDicesDTO, distance: ExecuteDistanceDTO):
        scores = []
        for candidate in distance.players_options:
            features = self._build_feature_vector(execution, distance, candidate)
            with torch.no_grad():
                score = torch.sigmoid(self.target_model(features)).item()
            scores.append((score, candidate))
        return max(scores, key=lambda item: item[0])[1]

    def _predict_shots(
        self,
        execution: ExecuteDicesDTO,
        distance: ExecuteDistanceDTO,
        target_player,
    ) -> int:
        features = self._build_feature_vector(execution, distance, target_player)
        with torch.no_grad():
            logits = self.shot_model(features)
            shot_index = int(logits.argmax(dim=1).item()) + 1
        return min(3, max(1, shot_index))

    def _predict_confidence(
        self,
        execution: ExecuteDicesDTO,
        distance: ExecuteDistanceDTO,
        target_player,
    ):
        features = self._build_feature_vector(execution, distance, target_player)
        with torch.no_grad():
            score = torch.sigmoid(self.target_model(features)).item()
        return round(float(max(0.3, min(0.95, score))), 2)
