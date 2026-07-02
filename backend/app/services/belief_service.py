from app.dtos.character import IdentityDTO
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
