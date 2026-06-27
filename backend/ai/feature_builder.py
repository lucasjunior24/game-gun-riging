import numpy as np

from ai.schemas import GameState


def build_features(state: GameState, actor_id: int, target_id: int):
    actor = next(p for p in state.players if p.id == actor_id)
    target = next(p for p in state.players if p.id == target_id)

    return np.array(
        [
            actor.vida,
            target.vida,
            actor.distancia,
            target.distancia,
            target.suspeita,
            1 if target.papel_estimado == "xerife" else 0,
            1 if target.papel_estimado == "fora_da_lei" else 0,
        ]
    )
