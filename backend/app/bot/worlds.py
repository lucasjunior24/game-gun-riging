from itertools import permutations

from app.dtos.character import IdentityDTO
from app.engine.roles import ROLE_DISTRIBUTION
from app.engine.view import PlayerObservation

World = dict[int, IdentityDTO]  # assento -> papel


def known_roles(obs: PlayerObservation) -> World:
    """Papeis que o jogador sabe com certeza: o proprio, o Xerife e os mortos."""
    known: World = {obs.viewer_seat: obs.my_identity}
    for p in obs.players:
        if p.public_identity is not None:
            known[p.seat] = p.public_identity
    return known


def enumerate_worlds(obs: PlayerObservation) -> list[World]:
    """Todas as atribuicoes de papel aos jogadores ocultos compativeis com o que e publico."""
    known = known_roles(obs)
    bag = list(ROLE_DISTRIBUTION[len(obs.players)])
    for role in known.values():
        bag.remove(role)  # papeis ja conhecidos saem do saco

    hidden = [p.seat for p in obs.players if p.seat not in known]
    # set() remove repeticoes (FL, FL); sorted() deixa a ordem igual entre processos
    unique = sorted(set(permutations(bag)), key=lambda perm: [r.value for r in perm])
    worlds = []
    for perm in unique:
        world = dict(known)
        world.update(zip(hidden, perm))
        worlds.append(world)
    return worlds
