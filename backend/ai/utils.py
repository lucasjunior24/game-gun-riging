from collections import defaultdict


def build_attack_matrix(history):
    """
    Retorna:
    attacks[a][b] = quantas vezes A atacou B
    """
    attacks = defaultdict(lambda: defaultdict(int))

    for event in history:
        if event.action == "tiro":
            attacks[event.attacker_id][event.target_id] += 1

    return attacks
