import random

from app.bot.worlds import World
from app.engine.dice import Die
from app.engine.state import EnginePlayer, EngineState, TurnState
from app.engine.view import PlayerObservation


def determinize(obs: PlayerObservation, world: World, rng: random.Random) -> EngineState:
    """Monta um estado do motor a partir da observacao, para simular sem trapacear.

    - os papeis vem do `world` sorteado da crenca, e nao do estado real;
    - o `rng` e do agente, nunca o da partida (um clone do real rolaria os mesmos dados).
    """
    players = [
        EnginePlayer(
            seat=p.seat,
            user_id=p.user_id,
            user_name=p.user_name,
            identity=world[p.seat],
            max_life=p.max_life,
            life=p.life,
            is_bot=True,
            arrows=p.arrows,
            revealed=p.public_identity is not None,
        )
        for p in obs.players
    ]
    turn = TurnState(
        seat=obs.current_seat,
        dice=[Die(d.index, d.face, d.locked, d.resolved) for d in obs.dice],
        rolls_used=obs.rolls_used,
        phase=obs.phase,
    )
    return EngineState(
        game_id="sim",
        players=players,
        rng=rng,
        turn=turn,
        arrows_in_pile=obs.arrows_in_pile,
        round_number=obs.round_number,
        turn_number=obs.turn_number,
        status=obs.status,
    )
