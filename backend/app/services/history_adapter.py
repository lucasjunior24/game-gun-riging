from app.dtos.history import ActionTypeDTO, GameActionHistoryDTO
from app.engine.events import EventType
from app.engine.state import EngineState

_ACTION_TYPE_BY_EVENT = {
    EventType.SHOT: ActionTypeDTO.TIRO,
    EventType.GATLING: ActionTypeDTO.GATLING,
    EventType.BEER: ActionTypeDTO.CERVEJA,
    EventType.INDIAN_ATTACK: ActionTypeDTO.INDIOS,
    EventType.DYNAMITE_EXPLODED: ActionTypeDTO.DINAMITE,
    EventType.DEATH: ActionTypeDTO.MORTE,
}


def events_to_history(state: EngineState) -> list[GameActionHistoryDTO]:
    """Converte os eventos do motor em historico de acoes, so com identidades publicas."""
    history: list[GameActionHistoryDTO] = []
    for event in state.events:
        action_type = _ACTION_TYPE_BY_EVENT.get(event.type)
        if action_type is None:
            continue
        actor = state.players[event.actor_seat] if event.actor_seat is not None else None
        target = state.players[event.target_seat] if event.target_seat is not None else None
        history.append(
            GameActionHistoryDTO(
                game_id=state.game_id,
                round_number=event.round_number,
                turn_number=event.turn_number,
                actor_user_name=actor.user_name if actor else "",
                actor_identity=event.actor_public_identity,
                action_type=action_type,
                target_user_name=target.user_name if target else "",
                target_identity=event.target_public_identity,
                shots=event.amount if action_type in (ActionTypeDTO.TIRO, ActionTypeDTO.GATLING) else 0,
            )
        )
    return history
