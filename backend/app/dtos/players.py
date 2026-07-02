from typing import Optional
from pydantic import Field, field_validator

from app.dtos.base import DTO, BaseDTO
from app.dtos.character import CharacterDTO, IdentityDTO
from app.dtos.session import SessionDTO


class IdentityProbabilityDTO(BaseDTO):
    xerife: float = Field(default=0.0, alias=IdentityDTO.XERIFE.value)
    fora_da_lei: float = Field(default=0.0, alias=IdentityDTO.FORA_DA_LEI.value)
    renegado: float = Field(default=0.0, alias=IdentityDTO.RENEGADO.value)
    assistente: float = Field(default=0.0, alias=IdentityDTO.ASSISTENTE.value)

    @classmethod
    def revealed_sheriff(cls) -> "IdentityProbabilityDTO":
        return cls(xerife=1.0)

    @classmethod
    def neutral_hidden(cls) -> "IdentityProbabilityDTO":
        return cls(fora_da_lei=1.0 / 3.0, renegado=1.0 / 3.0, assistente=1.0 / 3.0)

    def probability_for(self, identity: IdentityDTO) -> float:
        if identity == IdentityDTO.XERIFE:
            return self.xerife
        if identity == IdentityDTO.FORA_DA_LEI:
            return self.fora_da_lei
        if identity == IdentityDTO.RENEGADO:
            return self.renegado
        if identity == IdentityDTO.ASSISTENTE:
            return self.assistente
        raise ValueError(f"Identidade invalida: {identity}")

    def with_probability(
        self, identity: IdentityDTO, probability: float
    ) -> "IdentityProbabilityDTO":
        data = self.model_dump()
        if identity == IdentityDTO.XERIFE:
            data["xerife"] = probability
        elif identity == IdentityDTO.FORA_DA_LEI:
            data["fora_da_lei"] = probability
        elif identity == IdentityDTO.RENEGADO:
            data["renegado"] = probability
        elif identity == IdentityDTO.ASSISTENTE:
            data["assistente"] = probability
        else:
            raise ValueError(f"Identidade invalida: {identity}")
        return IdentityProbabilityDTO(**data)

    def total(self) -> float:
        return self.xerife + self.fora_da_lei + self.renegado + self.assistente


class PlayerDTO(BaseDTO):
    user_id: int = Field(default=0)
    user_name: str = Field(default="")
    # disabled: bool = Field(default=False)
    position: int = Field(default=0)
    # admin: bool = Field(default=False)
    # admin_master: bool = Field(default=False)
    # session: list[SessionDTO] = Field(...)
    is_alive: bool = Field(default=True)
    is_bot: bool = Field(default=True)
    arrow: int = Field(default=0)
    bullet: int = Field(default=0)
    papel_probability: IdentityProbabilityDTO = Field(
        default_factory=IdentityProbabilityDTO
    )
    character: Optional[CharacterDTO] = Field(default=None)
    # identity: Identity

    # team: Team

    @field_validator("papel_probability", mode="before")
    @classmethod
    def normalize_papel_probability(cls, value):
        if isinstance(value, IdentityProbabilityDTO):
            return value
        if value is None or isinstance(value, (int, float)):
            return IdentityProbabilityDTO()
        return value
