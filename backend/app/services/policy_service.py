from pathlib import Path
import torch

from app.dtos.character import IdentityDTO
from app.dtos.dice import ExecuteDicesDTO, ExecuteDistanceDTO, UserBulletsDTO
from app.dtos.players import PlayerDTO
from app.dtos.policy import ShotPolicyDecisionDTO, ShotPolicyPredictionDTO
from app.services.belief_service import BeliefService


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
        self.belief_service = BeliefService()
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

            target_player = self._predict_target(execution, distance, distance_label)
            if self.shot_model is None:
                shots = self._predict_shots_by_belief(distance, target_player)
            else:
                shots = self._predict_shots(execution, distance, target_player)

            if self.target_model is None:
                confidence = self._predict_confidence_by_belief(
                    execution, distance, distance_label, target_player
                )
            else:
                confidence = self._predict_confidence(
                    execution, distance, distance_label, target_player
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
            distance = self.get_execution_distance(execution, decision.distance)
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
            (
                1.0
                if self._get_current_identity(execution) == IdentityDTO.XERIFE
                else 0.0
            ),
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

    def _predict_target(
        self,
        execution: ExecuteDicesDTO,
        distance: ExecuteDistanceDTO,
        distance_label: str,
    ):
        scores = []
        for candidate in distance.players_options:
            belief_score = self._score_candidate_by_belief(
                execution, distance, distance_label, candidate
            )
            score = self._normalize_score(belief_score)
            if self.target_model is not None:
                features = self._build_feature_vector(execution, distance, candidate)
                with torch.no_grad():
                    neural_score = torch.sigmoid(self.target_model(features)).item()
                score = neural_score * 0.35 + score * 0.65
            scores.append((score, candidate))
        return max(scores, key=lambda item: item[0])[1]

    def _score_candidate_by_belief(
        self,
        execution: ExecuteDicesDTO,
        distance: ExecuteDistanceDTO,
        distance_label: str,
        candidate: PlayerDTO,
    ) -> float:
        if not candidate.is_alive:
            return -2.0
        if execution.current_player.user_name == candidate.user_name:
            return -2.0

        current_identity = self._get_current_identity(execution)
        if current_identity is None:
            identity_score = 0.0
        else:
            sheriff_user_name = self._get_revealed_sheriff_user_name(execution)
            identity_score = sum(
                self.belief_service.get_identity_probability(
                    candidate, identity, sheriff_user_name
                )
                * self._get_target_weight(current_identity, identity)
                for identity in IdentityDTO
            )

        life_score = max(0.0, min(1.0, (3.0 - float(candidate.bullet)) / 3.0))
        arrow_score = max(0.0, min(1.0, float(candidate.arrow) / 3.0))
        distance_score = 1.0 if distance_label == "1" else 0.6
        available_shots_score = max(0.0, min(1.0, float(distance.bullet_total) / 3.0))

        return (
            identity_score * 0.55
            + life_score * 0.20
            + arrow_score * 0.10
            + distance_score * 0.10
            + available_shots_score * 0.05
        )

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

    def _predict_shots_by_belief(
        self, distance: ExecuteDistanceDTO, target_player: PlayerDTO
    ) -> int:
        shots = min(3, max(1, distance.bullet_total))
        if target_player.bullet <= 1:
            return min(shots, 1)
        if target_player.bullet == 2:
            return min(shots, 2)
        return shots

    def _predict_confidence(
        self,
        execution: ExecuteDicesDTO,
        distance: ExecuteDistanceDTO,
        distance_label: str,
        target_player,
    ):
        features = self._build_feature_vector(execution, distance, target_player)
        with torch.no_grad():
            score = torch.sigmoid(self.target_model(features)).item()
        belief_score = self._normalize_score(
            self._score_candidate_by_belief(
                execution, distance, distance_label, target_player
            )
        )
        confidence = score * 0.35 + belief_score * 0.65
        return round(float(max(0.3, min(0.95, confidence))), 2)

    def _predict_confidence_by_belief(
        self,
        execution: ExecuteDicesDTO,
        distance: ExecuteDistanceDTO,
        distance_label: str,
        target_player: PlayerDTO,
    ) -> float:
        score = self._normalize_score(
            self._score_candidate_by_belief(
                execution, distance, distance_label, target_player
            )
        )
        return round(float(max(0.3, min(0.95, score))), 2)

    def _normalize_score(self, score: float) -> float:
        return max(0.0, min(1.0, (score + 1.0) / 2.0))

    def _get_target_weight(
        self, current_identity: IdentityDTO, target_identity: IdentityDTO
    ) -> float:
        if current_identity == IdentityDTO.XERIFE:
            if target_identity == IdentityDTO.FORA_DA_LEI:
                return 1.0
            if target_identity == IdentityDTO.RENEGADO:
                return 0.4
            if target_identity == IdentityDTO.ASSISTENTE:
                return -0.8
            return -1.0

        if current_identity == IdentityDTO.ASSISTENTE:
            if target_identity == IdentityDTO.FORA_DA_LEI:
                return 1.0
            if target_identity == IdentityDTO.RENEGADO:
                return 0.5
            if target_identity == IdentityDTO.ASSISTENTE:
                return -0.7
            return -1.0

        if current_identity == IdentityDTO.FORA_DA_LEI:
            if target_identity == IdentityDTO.XERIFE:
                return 1.0
            if target_identity == IdentityDTO.ASSISTENTE:
                return 0.8
            if target_identity == IdentityDTO.RENEGADO:
                return 0.3
            return -0.8

        if current_identity == IdentityDTO.RENEGADO:
            if target_identity == IdentityDTO.XERIFE:
                return 0.6
            if target_identity == IdentityDTO.FORA_DA_LEI:
                return 0.4
            if target_identity == IdentityDTO.ASSISTENTE:
                return 0.3
            return -0.6

        return 0.0

    def _get_current_identity(self, execution: ExecuteDicesDTO) -> IdentityDTO | None:
        if not execution.current_identity:
            return None
        return self.belief_service.coerce_identity(execution.current_identity)

    def _get_revealed_sheriff_user_name(self, execution: ExecuteDicesDTO) -> str | None:
        if self._get_current_identity(execution) == IdentityDTO.XERIFE:
            return execution.current_player.user_name

        for distance_label in ("1", "2"):
            distance = self.get_execution_distance(execution, distance_label)
            if not distance:
                continue
            for player in distance.players_options:
                if self.belief_service.is_revealed_sheriff(player):
                    return player.user_name
        return None
