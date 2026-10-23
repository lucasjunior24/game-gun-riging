from app.engine.state import TurnPhase


def force_dice(service, game_id, faces):
    """Define as faces dos dados direto no motor e entra na fase de resolucao.

    Usado para controlar o resultado dos dados nos testes do adaptador,
    sem depender do RNG real do motor.
    """
    state = service._games[game_id]
    for index, face in enumerate(faces):
        state.turn.dice[index].face = face
        state.turn.dice[index].locked = False
    state.turn.rolls_used = 1
    state.turn.phase = TurnPhase.RESOLVING
    return state
