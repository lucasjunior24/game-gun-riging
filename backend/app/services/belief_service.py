from app.dtos.character import IdentityDTO
from app.dtos.history import ActionTypeDTO, GameActionHistoryDTO
from app.dtos.players import IdentityProbabilityDTO, PlayerDTO


class BeliefService:
    IDENTITIES = tuple(IdentityDTO)
    HIDDEN_IDENTITIES = (
        IdentityDTO.FORA_DA_LEI,
        IdentityDTO.RENEGADO,
        IdentityDTO.ASSISTENTE,
    )

    def initialize_player_belief(
        self, player: PlayerDTO, sheriff_user_name: str | None = None
    ) -> IdentityProbabilityDTO:
        if self.is_revealed_sheriff(player, sheriff_user_name):
            return IdentityProbabilityDTO.revealed_sheriff()

        probabilities = player.papel_probability
        if probabilities.total() <= 0:
            probabilities = IdentityProbabilityDTO.neutral_hidden()

        if sheriff_user_name:
            probabilities = probabilities.with_probability(IdentityDTO.XERIFE, 0.0)

        return self.normalize(probabilities)

    def normalize(
        self, probabilities: IdentityProbabilityDTO
    ) -> IdentityProbabilityDTO:
        sanitized = IdentityProbabilityDTO(
            xerife=max(0.0, probabilities.xerife),
            fora_da_lei=max(0.0, probabilities.fora_da_lei),
            renegado=max(0.0, probabilities.renegado),
            assistente=max(0.0, probabilities.assistente),
        )
        total = sanitized.total()
        if total <= 0:
            return IdentityProbabilityDTO.neutral_hidden()
        return IdentityProbabilityDTO(
            xerife=sanitized.xerife / total,
            fora_da_lei=sanitized.fora_da_lei / total,
            renegado=sanitized.renegado / total,
            assistente=sanitized.assistente / total,
        )

    def coerce_identity(self, value: IdentityDTO | str) -> IdentityDTO:
        if isinstance(value, IdentityDTO):
            return value

        normalized = str(value).strip()
        for identity in self.IDENTITIES:
            if normalized == identity.value or normalized.upper() == identity.name:
                return identity

        raise ValueError(f"Identidade invalida: {value}")

    def parse_probabilities(
        self, raw: dict[str, float] | None
    ) -> IdentityProbabilityDTO:
        if not raw:
            return IdentityProbabilityDTO()

        probabilities = IdentityProbabilityDTO()
        for key, value in raw.items():
            identity = self.coerce_identity(key)
            probabilities = probabilities.with_probability(identity, float(value))
        return probabilities

    def get_identity_probability(
        self,
        player: PlayerDTO,
        identity: IdentityDTO,
        sheriff_user_name: str | None = None,
    ) -> float:
        probabilities = self.initialize_player_belief(player, sheriff_user_name)
        return probabilities.probability_for(identity)

    def get_most_likely_identity(
        self, player: PlayerDTO, sheriff_user_name: str | None = None
    ) -> IdentityDTO:
        probabilities = self.initialize_player_belief(player, sheriff_user_name)
        return max(
            self.IDENTITIES,
            key=lambda identity: probabilities.probability_for(identity),
        )

    def is_revealed_sheriff(
        self, player: PlayerDTO, sheriff_user_name: str | None = None
    ) -> bool:
        if sheriff_user_name and player.user_name == sheriff_user_name:
            return True

        return player.papel_probability.xerife >= 1.0

    def identity_key(self, identity: IdentityDTO) -> str:
        return identity.value

    def update_beliefs_from_history(
        self,
        players: list[PlayerDTO],
        action_history: list[GameActionHistoryDTO],
        sheriff_user_name: str | None = None,
    ) -> None:
        sheriff_user_name = self._resolve_sheriff_user_name(
            players, action_history, sheriff_user_name
        )
        for player in players:
            player.papel_probability = self.initialize_player_belief(
                player, sheriff_user_name
            )

        for action in action_history:
            actor = self._find_player(players, action.actor_user_name)
            if actor is None:
                continue

            if self._is_sheriff_action_actor(action, actor, sheriff_user_name):
                actor.papel_probability = IdentityProbabilityDTO.revealed_sheriff()
                continue

            target = self._find_player(players, action.target_user_name)
            updated = actor.papel_probability

            if self._is_action_type(action, ActionTypeDTO.TIRO) or self._is_action_type(
                action, ActionTypeDTO.GATLING
            ):
                updated = self._apply_attack_belief_update(
                    updated, action, target, sheriff_user_name
                )
            elif self._is_action_type(action, ActionTypeDTO.CERVEJA):
                updated = self._apply_help_belief_update(
                    updated, action, target, sheriff_user_name
                )

            if sheriff_user_name:
                updated = updated.with_probability(IdentityDTO.XERIFE, 0.0)
            actor.papel_probability = self.normalize(updated)

    def _apply_attack_belief_update(
        self,
        probabilities: IdentityProbabilityDTO,
        action: GameActionHistoryDTO,
        target: PlayerDTO | None,
        sheriff_user_name: str | None,
    ) -> IdentityProbabilityDTO:
        if self._is_sheriff_action_target(action, target, sheriff_user_name):
            return self._adjust_probabilities(
                probabilities,
                outlaw_delta=0.25,
                renegade_delta=0.08,
                assistant_delta=-0.20,
            )

        target_outlaw_probability = 0.0
        if target is not None:
            target_outlaw_probability = self.get_identity_probability(
                target, IdentityDTO.FORA_DA_LEI, sheriff_user_name
            )
        if target_outlaw_probability >= 0.6:
            return self._adjust_probabilities(
                probabilities,
                outlaw_delta=-0.12,
                renegade_delta=0.02,
                assistant_delta=0.18,
            )

        return self._adjust_probabilities(
            probabilities,
            outlaw_delta=0.04,
            renegade_delta=0.03,
            assistant_delta=-0.02,
        )

    def _apply_help_belief_update(
        self,
        probabilities: IdentityProbabilityDTO,
        action: GameActionHistoryDTO,
        target: PlayerDTO | None,
        sheriff_user_name: str | None,
    ) -> IdentityProbabilityDTO:
        if self._is_sheriff_action_target(action, target, sheriff_user_name):
            return self._adjust_probabilities(
                probabilities,
                outlaw_delta=-0.15,
                renegade_delta=-0.02,
                assistant_delta=0.25,
            )
        return self._adjust_probabilities(probabilities, assistant_delta=0.05)

    def _adjust_probabilities(
        self,
        probabilities: IdentityProbabilityDTO,
        outlaw_delta: float = 0.0,
        renegade_delta: float = 0.0,
        assistant_delta: float = 0.0,
    ) -> IdentityProbabilityDTO:
        return IdentityProbabilityDTO(
            xerife=probabilities.xerife,
            fora_da_lei=probabilities.fora_da_lei + outlaw_delta,
            renegado=probabilities.renegado + renegade_delta,
            assistente=probabilities.assistente + assistant_delta,
        )

    def _resolve_sheriff_user_name(
        self,
        players: list[PlayerDTO],
        action_history: list[GameActionHistoryDTO],
        sheriff_user_name: str | None,
    ) -> str | None:
        if sheriff_user_name:
            return sheriff_user_name

        for player in players:
            if self.is_revealed_sheriff(player):
                return player.user_name

        for action in action_history:
            if self._is_identity(action.actor_identity, IdentityDTO.XERIFE):
                return action.actor_user_name
            if self._is_identity(action.target_identity, IdentityDTO.XERIFE):
                return action.target_user_name

        return None

    def _is_sheriff_action_actor(
        self,
        action: GameActionHistoryDTO,
        actor: PlayerDTO,
        sheriff_user_name: str | None,
    ) -> bool:
        return (
            self._is_identity(action.actor_identity, IdentityDTO.XERIFE)
            or self.is_revealed_sheriff(actor, sheriff_user_name)
        )

    def _is_sheriff_action_target(
        self,
        action: GameActionHistoryDTO,
        target: PlayerDTO | None,
        sheriff_user_name: str | None,
    ) -> bool:
        if self._is_identity(action.target_identity, IdentityDTO.XERIFE):
            return True
        if target is None:
            return False
        return self.is_revealed_sheriff(target, sheriff_user_name)

    def _find_player(
        self, players: list[PlayerDTO], user_name: str
    ) -> PlayerDTO | None:
        for player in players:
            if player.user_name == user_name:
                return player
        return None

    def _is_identity(
        self, value: IdentityDTO | str | None, identity: IdentityDTO
    ) -> bool:
        if value is None:
            return False
        return self.coerce_identity(value) == identity

    def _is_action_type(
        self, action: GameActionHistoryDTO, action_type: ActionTypeDTO
    ) -> bool:
        return action.action_type == action_type or action.action_type == action_type.value
