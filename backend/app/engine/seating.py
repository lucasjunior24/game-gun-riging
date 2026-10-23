from app.engine.dice import DiceFace
from app.engine.state import EngineState


def distance(state: EngineState, from_seat: int, to_seat: int) -> int:
    alive = [p.seat for p in state.players if p.is_alive]
    i, j = alive.index(from_seat), alive.index(to_seat)
    steps = abs(i - j)
    return min(steps, len(alive) - steps)


def valid_targets(state: EngineState, shooter_seat: int, face: DiceFace) -> list[int]:
    alive = state.alive_players()
    if face is DiceFace.BEER:
        return [p.seat for p in alive]

    wanted = 1 if face is DiceFace.SHOT_1 else 2
    if len(alive) <= 3:
        wanted = 1
    return [
        p.seat
        for p in alive
        if p.seat != shooter_seat and distance(state, shooter_seat, p.seat) == wanted
    ]
