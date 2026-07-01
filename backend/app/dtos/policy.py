from typing import Literal
from pydantic import BaseModel, Field


class ShotPolicyDecisionDTO(BaseModel):
    target_user_name: str
    shots: int = Field(ge=1, le=3)
    distance: Literal["1", "2"]
    confidence: float = Field(default=0.0)


class ShotPolicyPredictionDTO(BaseModel):
    decisions: list[ShotPolicyDecisionDTO] = Field(default_factory=list)
