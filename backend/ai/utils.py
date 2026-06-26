from collections import defaultdict

from typing import List

from ai.schemas import Event, GameState


def build_attack_matrix(history: List[Event]):
    """
    Retorna:
    attacks[a][b] = quantas vezes A atacou B
    """
    attacks = defaultdict(lambda: defaultdict(int))

    for event in history:
        if event.action == "tiro":
            attacks[event.attacker_id][event.target_id] += 1

    return attacks


def predict_incoming_damage(state: GameState):
    """
    Estima quantos tiros cada player vai receber
    """
    incoming = {p.id: 0 for p in state.players}

    for p in state.players:

        if p.id == state.self_id:
            continue

        # probabilidade de atacar alguém
        for target in state.players:

            if target.id == p.id:
                continue

            # 🔥 chance baseada em suspeita
            prob_attack = target.suspeita

            # 🔫 assume 1 tiro esperado
            incoming[target.id] += prob_attack * 1

    return incoming
