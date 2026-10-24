from app.engine.dice import MAX_ROLLS
from app.engine.rules import TARGETED_FACES
from app.engine.seating import valid_targets
from app.engine.state import EngineState, GameStatus, TurnPhase

ROLL = "ROLL"
STOP_ROLLING = "STOP_ROLLING"
RESOLVE = "RESOLVE"
FINISH_TURN = "FINISH_TURN"
WAIT_BOTS = "WAIT_BOTS"


def allowed_actions(state: EngineState, seat: int) -> list[str]:
    if state.status is GameStatus.DONE:
        return []
    if state.turn.seat != seat:
        return [WAIT_BOTS] if state.current_player.is_bot else []
    turn = state.turn
    if turn.phase is TurnPhase.ROLLING:
        actions = [ROLL] if turn.rolls_used < MAX_ROLLS else []
        if turn.rolls_used > 0:
            actions.append(STOP_ROLLING)
        return actions
    pending = any(d.face in TARGETED_FACES and not d.resolved for d in turn.dice)
    return [RESOLVE] if pending else [FINISH_TURN]


def dice_targets(state: EngineState, seat: int) -> dict[int, list[int]]:
    """Para cada dado pendente, os assentos que ele pode atingir."""
    if state.status is GameStatus.DONE or state.turn.phase is not TurnPhase.RESOLVING:
        return {}
    return {
        d.index: valid_targets(state, seat, d.face)
        for d in state.turn.dice
        if d.face in TARGETED_FACES and not d.resolved
    }
