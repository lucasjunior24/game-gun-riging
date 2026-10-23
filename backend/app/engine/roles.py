import random

from app.dtos.character import IdentityDTO, TeamDTO

ROLE_DISTRIBUTION: dict[int, list[IdentityDTO]] = {
    4: [
        IdentityDTO.XERIFE,
        IdentityDTO.RENEGADO,
        IdentityDTO.FORA_DA_LEI,
        IdentityDTO.FORA_DA_LEI,
    ],
}
ROLE_DISTRIBUTION[5] = ROLE_DISTRIBUTION[4] + [IdentityDTO.ASSISTENTE]
ROLE_DISTRIBUTION[6] = ROLE_DISTRIBUTION[5] + [IdentityDTO.FORA_DA_LEI]
ROLE_DISTRIBUTION[7] = ROLE_DISTRIBUTION[6] + [IdentityDTO.ASSISTENTE]
ROLE_DISTRIBUTION[8] = ROLE_DISTRIBUTION[7] + [IdentityDTO.RENEGADO]


def deal_roles(
    players_total: int, rng: random.Random, shuffle: bool = True
) -> list[IdentityDTO]:
    if players_total not in ROLE_DISTRIBUTION:
        raise ValueError("Bang! Dice suporta de 4 a 8 jogadores")
    roles = list(ROLE_DISTRIBUTION[players_total])
    if shuffle:
        rng.shuffle(roles)
    return roles


def team_for(identity: IdentityDTO) -> TeamDTO:
    if identity in (IdentityDTO.XERIFE, IdentityDTO.ASSISTENTE):
        return TeamDTO.XERIFE
    if identity is IdentityDTO.FORA_DA_LEI:
        return TeamDTO.FORA_DA_LEI
    return TeamDTO.RENEGADO
