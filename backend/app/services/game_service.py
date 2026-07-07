from dataclasses import dataclass, field
from uuid import uuid4

from app.dtos.character import CharacterDTO, IdentityDTO, TeamDTO
from app.dtos.game_state import (
    CreateAuthoritativeGameDTO,
    ExecuteShotsCommandDTO,
    GameStateDTO,
    InternalPlayerDTO,
    PublicPlayerDTO,
)
from app.dtos.history import ActionTypeDTO, GameActionHistoryDTO
from app.dtos.players import IdentityProbabilityDTO, PlayerDTO
from app.services.belief_service import BeliefService


def _team_for_identity(identity: IdentityDTO) -> TeamDTO:
    if identity == IdentityDTO.ASSISTENTE:
        return TeamDTO.XERIFE
    if identity == IdentityDTO.XERIFE:
        return TeamDTO.XERIFE
    if identity == IdentityDTO.FORA_DA_LEI:
        return TeamDTO.FORA_DA_LEI
    return TeamDTO.RENEGADO


def _identity_equals(value: IdentityDTO | str, identity: IdentityDTO) -> bool:
    return value == identity or value == identity.value


def _team_equals(value: TeamDTO | str, team: TeamDTO) -> bool:
    return value == team or value == team.value


@dataclass
class InternalGameState:
    game_id: str
    players: list[InternalPlayerDTO]
    current_player_index: int = 0
    round_number: int = 1
    turn_number: int = 1
    status: str = "Running"
    winner: TeamDTO | None = None
    action_history: list[GameActionHistoryDTO] = field(default_factory=list)


class GameService:
    _games: dict[str, InternalGameState] = {}

    def __init__(self):
        self.belief_service = BeliefService()

    def create_game(self, command: CreateAuthoritativeGameDTO) -> GameStateDTO:
        game_id = str(uuid4())
        players = self._create_players(command.player_name, command.players_total)
        state = InternalGameState(game_id=game_id, players=players)
        self._refresh_beliefs(state)
        self._games[game_id] = state
        return self.to_public_state(state)

    def get_state(self, game_id: str) -> GameStateDTO:
        return self.to_public_state(self._get_game(game_id))

    def execute_shots(
        self, game_id: str, command: ExecuteShotsCommandDTO
    ) -> GameStateDTO:
        state = self._get_game(game_id)
        actor = self._find_player_by_id(state.players, command.actor_user_id)

        for distance in command.shots_by_distance:
            for user_bullets in distance.user_bullets:
                if user_bullets.shots <= 0:
                    continue
                target = self._find_player_by_name(state.players, user_bullets.user_name)
                if not target or not target.is_alive:
                    continue

                life_before = target.bullet
                target.bullet = max(0, target.bullet - user_bullets.shots)
                target.is_alive = target.bullet > 0

                state.action_history.append(
                    GameActionHistoryDTO(
                        game_id=state.game_id,
                        round_number=state.round_number,
                        turn_number=state.turn_number,
                        actor_user_name=actor.user_name,
                        actor_identity=actor.identity,
                        action_type=ActionTypeDTO.TIRO,
                        target_user_name=target.user_name,
                        target_identity=target.identity,
                        distance=distance.distance,
                        shots=user_bullets.shots,
                        target_life_before=life_before,
                        target_life_after=target.bullet,
                    )
                )

        state.players = [player for player in state.players if player.is_alive]
        self._refresh_beliefs(state)
        self._resolve_winner(state)
        if state.status == "Running":
            self._advance_turn(state)
        return self.to_public_state(state)

    def finish_turn(self, game_id: str) -> GameStateDTO:
        state = self._get_game(game_id)
        self._advance_turn(state)
        return self.to_public_state(state)

    def to_public_state(self, state: InternalGameState) -> GameStateDTO:
        current_player = state.players[state.current_player_index]
        return GameStateDTO(
            game_id=state.game_id,
            status=state.status,
            round_number=state.round_number,
            turn_number=state.turn_number,
            current_player=self._to_public_player(current_player),
            current_player_index=state.current_player_index,
            players=[self._to_public_player(player) for player in state.players],
            available_actions=self._available_actions(state),
            winner=state.winner,
        )

    def _create_players(
        self, player_name: str, players_total: int
    ) -> list[InternalPlayerDTO]:
        names = [player_name, "Murilo", "Aragao", "Roberto", "Pedro"][:players_total]
        identities = [
            IdentityDTO.XERIFE,
            IdentityDTO.FORA_DA_LEI,
            IdentityDTO.FORA_DA_LEI,
            IdentityDTO.RENEGADO,
            IdentityDTO.ASSISTENTE,
        ][:players_total]
        characters = self._default_characters()

        players: list[InternalPlayerDTO] = []
        for index, identity in enumerate(identities):
            character = characters[index % len(characters)]
            probability = (
                IdentityProbabilityDTO.revealed_sheriff()
                if identity == IdentityDTO.XERIFE
                else IdentityProbabilityDTO.neutral_hidden()
            )
            players.append(
                InternalPlayerDTO(
                    user_id=index + 1,
                    user_name=names[index],
                    position=index + 1,
                    character=character,
                    is_alive=True,
                    is_bot=index > 0,
                    arrow=0,
                    bullet=character.initial_bullet,
                    revealed_identity=(
                        IdentityDTO.XERIFE
                        if _identity_equals(identity, IdentityDTO.XERIFE)
                        else None
                    ),
                    identity=identity,
                    team=_team_for_identity(identity),
                    papel_probability=probability,
                )
            )
        return players

    def _default_characters(self) -> list[CharacterDTO]:
        return [
            CharacterDTO(initial_bullet=8, character="Janet Calamidade", power=""),
            CharacterDTO(initial_bullet=8, character="El Gringo", power=""),
            CharacterDTO(initial_bullet=11, character="Sid Vicious", power=""),
            CharacterDTO(initial_bullet=9, character="Paul Regret", power=""),
            CharacterDTO(initial_bullet=10, character="Jourdonnais", power=""),
        ]

    def _to_public_player(self, player: InternalPlayerDTO) -> PublicPlayerDTO:
        return PublicPlayerDTO(
            user_id=player.user_id,
            user_name=player.user_name,
            position=player.position,
            character=player.character,
            is_alive=player.is_alive,
            is_bot=player.is_bot,
            arrow=player.arrow,
            bullet=player.bullet,
            revealed_identity=(
                IdentityDTO.XERIFE
                if _identity_equals(player.identity, IdentityDTO.XERIFE)
                else None
            ),
        )

    def _refresh_beliefs(self, state: InternalGameState) -> None:
        sheriff = self._get_sheriff(state.players)
        players = [self._as_player_dto(player) for player in state.players]
        self.belief_service.update_beliefs_from_history(
            players,
            state.action_history,
            sheriff.user_name if sheriff else None,
        )
        for player in state.players:
            updated = self._find_player_dto_by_name(players, player.user_name)
            if updated:
                player.papel_probability = updated.papel_probability

    def _resolve_winner(self, state: InternalGameState) -> None:
        sheriff = self._get_sheriff(state.players)
        outlaws = [
            player
            for player in state.players
            if _team_equals(player.team, TeamDTO.FORA_DA_LEI)
        ]
        renegades = [
            player
            for player in state.players
            if _identity_equals(player.identity, IdentityDTO.RENEGADO)
        ]

        if sheriff and not outlaws and not renegades:
            state.status = "Done"
            state.winner = TeamDTO.XERIFE
        elif not sheriff:
            state.status = "Done"
            state.winner = TeamDTO.FORA_DA_LEI

    def _advance_turn(self, state: InternalGameState) -> None:
        if not state.players:
            return
        state.current_player_index += 1
        if state.current_player_index >= len(state.players):
            state.current_player_index = 0
            state.round_number += 1
        state.turn_number += 1

    def _available_actions(self, state: InternalGameState) -> list[str]:
        if state.status != "Running":
            return []
        return ["ROLL_DICE", "SHOOT", "FINISH_TURN"]

    def _get_game(self, game_id: str) -> InternalGameState:
        game = self._games.get(game_id)
        if game is None:
            raise KeyError(f"Partida nao encontrada: {game_id}")
        return game

    def _get_sheriff(
        self, players: list[InternalPlayerDTO]
    ) -> InternalPlayerDTO | None:
        for player in players:
            if _identity_equals(player.identity, IdentityDTO.XERIFE) and player.is_alive:
                return player
        return None

    def _find_player_by_id(
        self, players: list[InternalPlayerDTO], user_id: int
    ) -> InternalPlayerDTO:
        for player in players:
            if player.user_id == user_id:
                return player
        raise ValueError(f"Jogador nao encontrado: {user_id}")

    def _find_player_by_name(
        self, players: list[InternalPlayerDTO], user_name: str
    ) -> InternalPlayerDTO | None:
        for player in players:
            if player.user_name == user_name:
                return player
        return None

    def _as_player_dto(self, player: InternalPlayerDTO) -> PlayerDTO:
        dto = PlayerDTO(
            user_id=player.user_id,
            user_name=player.user_name,
            position=player.position,
            is_alive=player.is_alive,
            is_bot=player.is_bot,
            arrow=player.arrow,
            bullet=player.bullet,
            character=player.character,
        )
        dto.papel_probability = player.papel_probability
        return dto

    def _find_player_dto_by_name(
        self, players: list[PlayerDTO], user_name: str
    ) -> PlayerDTO | None:
        for player in players:
            if player.user_name == user_name:
                return player
        return None
