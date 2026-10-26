from collections.abc import Iterable, Mapping

from app.dtos.character import IdentityDTO, TeamDTO


def winner_for(alive_seats: Iterable[int], roles: Mapping[int, IdentityDTO]) -> TeamDTO | None:
    """Time vencedor dados os vivos e os papeis, ou None se a partida continua.

    Funcao pura: o bot usa com os papeis de cada mundo possivel, e nao com os reais.
    """
    alive_roles = [roles[seat] for seat in alive_seats]
    if IdentityDTO.XERIFE not in alive_roles:
        only_renegade = alive_roles == [IdentityDTO.RENEGADO]
        return TeamDTO.RENEGADO if only_renegade else TeamDTO.FORA_DA_LEI
    if not any(r in (IdentityDTO.FORA_DA_LEI, IdentityDTO.RENEGADO) for r in alive_roles):
        return TeamDTO.XERIFE
    return None
