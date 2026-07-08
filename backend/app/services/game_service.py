import random
from dataclasses import dataclass, field
from uuid import uuid4

from app.dtos.character import CharacterDTO, IdentityDTO, TeamDTO
from app.dtos.dice import (
    DiceShowDTO,
    ExecuteDicesDTO,
    ExecuteDistanceDTO,
    UserBulletsDTO,
)
from app.dtos.game_state import (
    BotTurnResultDTO,
    CreateAuthoritativeGameDTO,
    ExecuteShotsCommandDTO,
    GameStateDTO,
    InternalPlayerDTO,
    PublicPlayerDTO,
    RollDiceCommandDTO,
    ShootDistanceCommandDTO,
)
from app.dtos.history import ActionTypeDTO, GameActionHistoryDTO
from app.dtos.players import IdentityProbabilityDTO, PlayerDTO
from app.services.belief_service import BeliefService
from app.services.policy_service import ShotPolicyService


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
                target = self._find_player_by_name(
                    state.players, user_bullets.user_name
                )
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

    def get_dice_names(self, dice: str) -> str:
        if dice == "3":
            return "Dinamite"
        elif dice == "4":
            return "Cerveja"
        elif dice == "5":
            return "Flexa"
        elif dice == "6":
            return "Metralhadora"

        return dice

    def roll_dice(self, game_id: str, command: RollDiceCommandDTO) -> GameStateDTO:
        state = self._get_game(game_id)
        dice_map: dict[int, DiceShowDTO] = {
            dice.index: dice for dice in command.locked_dice_indexes
        }

        dice_faces = ["1", "2", "3", "4", "5", "6"]
        dice_results: list[DiceShowDTO] = []
        for i in range(5):
            current_dice = dice_map.get(i + 1, None)
            if current_dice and current_dice.locked:
                dice_results.append(current_dice)
                continue
            face = random.choice(dice_faces)
            dice = self.get_dice_names(face)
            dice_results.append(
                DiceShowDTO(
                    dice=int(face),
                    locked=True if dice == "Dinamite" else False,
                    show=dice,
                    index=i + 1,
                )
            )
        state.dice = dice_results
        return self.to_public_state(state)

    def execute_bot_turn(self, game_id: str) -> GameStateDTO:
        state = self._get_game(game_id)
        current = state.players[state.current_player_index]
        if not current.is_bot:
            raise ValueError(f"Jogador {current.user_name} nao e um bot")

        self._refresh_beliefs(state)

        sheriff = self._get_sheriff(state.players)
        sheriff_user_name = sheriff.user_name if sheriff else None

        alive_players = [p for p in state.players if p.is_alive]
        one_distance_players = [
            self._as_player_dto(p)
            for p in alive_players
            if p.user_id != current.user_id
        ]

        execution = ExecuteDicesDTO(
            game_id=state.game_id,
            current_player=self._as_player_dto(current),
            current_identity=str(current.identity) if current.identity else "",
            table_situation=f"round_{state.round_number}_turn_{state.turn_number}",
            one_distance=ExecuteDistanceDTO(
                bullet_total=current.bullet,
                players_options=one_distance_players,
            ),
            two_distance=None,
            action_history=list(state.action_history),
        )

        policy = ShotPolicyService()
        prediction = policy.predict(execution)

        for decision in prediction.decisions:
            target = self._find_player_by_name(state.players, decision.target_user_name)
            if not target or not target.is_alive:
                continue

            life_before = target.bullet
            target.bullet = max(0, target.bullet - decision.shots)
            target.is_alive = target.bullet > 0

            state.action_history.append(
                GameActionHistoryDTO(
                    game_id=state.game_id,
                    round_number=state.round_number,
                    turn_number=state.turn_number,
                    actor_user_name=current.user_name,
                    actor_identity=current.identity,
                    action_type=ActionTypeDTO.TIRO,
                    target_user_name=target.user_name,
                    target_identity=target.identity,
                    distance=decision.distance,
                    shots=decision.shots,
                    target_life_before=life_before,
                    target_life_after=target.bullet,
                )
            )

        state.players = [p for p in state.players if p.is_alive]
        self._refresh_beliefs(state)
        self._resolve_winner(state)
        if state.status == "Running":
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
            dice=state.dice if hasattr(state, "dice") else [],
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
            CharacterDTO(
                initial_bullet=8,
                character="Janet Calamidade",
                power="",
                avatar="data:image/jpeg;base64,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",
            ),
            CharacterDTO(
                initial_bullet=8,
                character="El Gringo",
                power="",
                avatar="data:image/jpeg;base64,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",
            ),
            CharacterDTO(
                initial_bullet=11,
                character="Willy the Kid",
                power="",
                avatar="data:image/jpeg;base64,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",
            ),
            CharacterDTO(
                initial_bullet=9,
                character="Paul ",
                power="",
                avatar="data:image/jpeg;base64,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",
            ),
            CharacterDTO(
                initial_bullet=10,
                character="Jourdonnais",
                power="",
                avatar="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxMTEhUTExMVFhUXGBcYGBgXFxUXFxgXFxgWFhcYFxcYHSggGBolHRgXITEhJSkrLi4uFx8zODMtOCgtLisBCgoKDg0OGBAQFy0dHyArLS0tLSstLS0rLS0tLS0tLS0tLS0tLS0tLS0tLSsrLS0tLS0tLS0tLS0tLS0rLS0tN//AABEIAJkBSQMBIgACEQEDEQH/xAAcAAABBQEBAQAAAAAAAAAAAAACAAEDBAYFBwj/xABEEAACAQIEAwUEBgYJBAMAAAABAhEAAwQSITEFQVEGEyJhkTJxgaEHQlJisdEUI3KSwfAVJENjgpOi0uEWM0SyVKPx/8QAGQEAAwEBAQAAAAAAAAAAAAAAAAECAwQF/8QAIxEAAgIBBAIDAQEAAAAAAAAAAAECEQMSITFBE1EEMmEiFP/aAAwDAQACEQMRAD8A84UmjVqhLUc1wnskqnSpLYqFdqK2+9IoeakDaVEBUtxtNKAodX1qdG1n8KqBqNCZpNAXgw3qW1f9KqK0DT41NabpUtDRaJ0qRXocOyuSocErEqNY9+tXVwU7Ny6f81LdDsinb1/CpkuxpUycKP2vl/zUycKjTMeX1R+dFoLKlq5+Pr0ort3+Hu0NXk4RqPEf3dfxqQ8EnTO37o/OlqQnI5C3NDVcXj6Vo07NyP8AuH90R/7UY7Jgf2rT+yI/GtFJGbkZs3dKj7yfX5VpW7LrEm6wHM5Vj8a5w4QhY5XfKN2gDTmY+Qo1oaOcHoHfar39G+b+gnzoP6Oj7fxFTqRZzrl2YqMvpXSbhon2m9AKjHDAd2b1FGpEtlJGOlPnArojhS82b/T+VM3DUI3b5flSckNSOSblQXn1Fdv+iE+0/wAMv5UjwC39p/VfyoU0h7nCDa0OSRpXfHALYnxPv1T/AG1Na4DbPhLuNDBld+U+HanrQrMqw3BpXNtq1lrsrbcFe9e3d5B8pQ+WwIPrWax+Fa07W3GVl0I9D896tOwTspNQh6kuGhZdKoQ4E0O1K0aTmgZGd6iapqiamiGJTTTQnekGpiDJpsx60pps1FASMdaLNTA0/KpKCD1JaNQ5akTQUMaJidKEmhY04bakOyS1ak05PiIoAx5Uy8yaAZObm9WeE63AD5n8K5zvXV7NqTd9yn8RSlwI4Vy9dwmKZmQAEkkD2WQmfCT/ADIrfcOxVu6oZGUgjlEj3gbfGoeO8LS9ZYODKgsrASVIBOnWY2rzng/EmsXUuLyPiE6MvNT/ADvV6VljfaORzeKVdM9isipUw2opYJg6K66ggEHyIq9bt1ytG+sGynWrlq3zoVta0N3iVm22VnGb7Ilm/dUEimot8GbkXEtVKgqhheNWGVmFwBVMEuGTWAY8YEmDsK5y9uMD3ot96ZzRmKMEnzc7e+I86tY5PolzXs5+IuNca4WchVYiBruxAAEgcudcfGdoERxZAcaZtNyBJkmRtB0q6P7fp3g0H7Tn03rg8bulMtyY0uJsN2UFd9tRSgk3TN5NqNosjtEvhg3IcwNVOoIXWH86B+0axOdomNLi7xPJ6pYDL3wsLm/VF3jSIKJEHf67elVLnFbfdTmaP0nNoEAjMXPyrXxRvgy8kq3O9iOIgOtsmWYiPEJ105mapP2itBSYuQGybL7UE6eLy+dUb/aKy1xGlgql5MDUFQNt9+VT4XiNt79sAnxoTlgFcwnKx03yg6+6l46W6Bzt7Mt8S4ytlgpRixAPhjmSBz30p7PGQ8AKQWBIzMgOgO6lpHTaKLjrqiZmbJ4rZB0k5GzkTB5Zj76p4rHIMVaUZ1/VufCEA8Xj2IO4U/GKIxjJLYUpOL5J73aFFVWCs4ZiBlKtqMvMHnJ9Kt4bi4a0b2VgA2Uq5VGEAEzJgbjes5g+LIuGSWujLd+qEmJL78tGHxmunb4mjYS8QXYAFJ0FxswUS3KfF56CnLEl12OORvvo6X9Mrr4RIXOQGB00128z5aUJ40pCELOYEqM2pEkaDLJ5Gdta5eG4sqmT3pD4dWBkEjJ3gZc2gG2mnM1Bb4yqJhmIveAMrZYOwyajTnEbaU/GvRLm/ZrMHjlu2wYBGo8wQSCJ94I1FZ3teIv7mCi6nUxGgPXSurwLEh7ZYAgNcuMM28M5bX1rm9uB+stHrbHyAFZRVTo6Iy2sz/OiBqDvKYNW1D1Eg0NEza/CgbaabNSGOTUbbUTNvQzTQmC5oZp2NRGrRmyUNTwehoFOo6V0v6QX7HzpMEUaNdqCKOpZaCJ2qQnT41DNEDSY0SHWmU0M0M0wbJg1DNK2KRGtAw4rR9kkl20+qPx/4rMhq1PY1f8AuEfdH4n+NRPgRq+6EEcjP4dK8Y4rgTYvPaYglGiRseY+XKvYceWWzcZDDBHIPQhSQdq8kbEN3jHSWJnMSTr1J3+NafH4Zx592j0z6O8W1zChTl/VwojeInXz861oMakwBqSdAOsnpXmXYDirJf7ogBbjAEDZWyyjDyMQfeOlbbtgjfoOIyzITN5wGVm+QNZzhc69jUv5K+K433xy2Wy29i40Z/JOar97c8o3M1m0ioQoC+nxn39d68w4dx8pvqZnqKnx3a9oyqBJ58h8K64wUdkc7lbsr4Tj920HCmSSwBOpWSSch5SfwrjvcJ6zVcsetLWAdY1g8pG+vxqybNPwPiA7tbDAsWu28smAq+NW1mZ1EVobxyEBjmT7TCSp+9PL73nr1rzjvD/PrWo7KYye87xi0lfaJOkMCNTtrUSxpqjSOWSZqEjfb4fzpUhtrHsj0HuiqGAuApGrQSAZ5KxAPpVyR/MV50rTo9FbqyUqI9lfQctv4UzNHJfTn/P40Iuj7Pzpd8OnzqLLpB95ry9KMXJ0gegqMEb5SB8akQr0Pr/xSticTl9o+L/o9vMFBdjlWRoOpOusdPdWafF4vL336RPgW4VgZcrNAAEZc3kK0PavhRxFsd2DnQyASNQdCAdNdvSsy2LfL3RsXA3dC1kynLMz3sb5v5mu7BWg4c1qRpuCcd7213jKikSH0MSBM77c6tcD48b4c92qhTAJk5h/Dl61lcRgL1jCrbghrzy5+qoIACE9TuT5RXe4JdtC2tu04bJo0bzJknyJms8kIpNrtmuOTbSfo0aXC2iohMcl10+NZ3tyulgwBAdTl/wkc/L8a0XD8GbrBASFiWPl8d9arfSLg0TD2sixFyJ3OqNuf8NY43/SNWecMKQqQprTZa67CgkaRQA0YFRtvSGOtPPKnY0woABxQNUpqI00SxA09IU9MEOOtSq01ApqRTpUsaDanBqPNSJ1pUOwj0ogajBpxTESq1OaBTSzUh2GorX9jAMjn70egX86x55VtOx6xZnqzH8B/Cs8nAM0GMQtZuAAElHADbElTAPlXi95deXLWa9tTX8q83+kLhFixctm14WuZiUnwqAQAw5qDrvpppWnx30cmZdnI4NjWsXEubgXEYxBkIZIE+8ivaeCcVsYu0WtsHU+FlOjCRBVl5EisN2V7LWrSm/irltiqN3NlTmzO4ZRM+2ZOgGk6zpXAxWFxXDSGtXWTvLdtpWPEpidwRIJ+Z61rKCnwZqTiXO1/YG7hpu2Ju2BqRpnQfeH1lH2h8ayVpMyEAeLMJOmxgLAP3p9a1/COOtisQi4tUfPbyI5RQSVJIk9dW1EaxWWxloC/cVRABYAAdOXyrRXW5FW9jvcf7PNw9bMsWuXrQdhlAVTPsgmQ4UgSIG3mK6WPwz4mzgMFZsKD+j/AKR95mcuDqSNCELHc6+Va3jeEtXOF2GxRe93dkQUANwtdtqinU8jBk/ZpdjOJj9Eu4q6jvewqNbt94qLFsKGypkA6QTuIrPybWX49zyftFwo4a73TEEhVJgEakagg7H/APedW+y/B7+Kbu7CFmJ1JkIo3l22X8ao8Yx17E3ma54rjsdFESWgACN9AFHkBXv3YVGXDBGW2uRnT9WgRTlMSQPrTmk1U56Y2TGNyM5w/sfiLdtUyYc5RuS0k7kmB151ZHZvEHe3h/V627CmavPbt2dim6ox6dm732cP/qM9eVSr2auxP9XB5Rbn5kTWp+NOH5UlQeSRlR2duDd7I91ofkKzuL4ng7VvvDi7LDYKlvM51j2DBAjmYrsfSN2oSxYeyjTeuAKQPqIw8RY/VJGg56zXkGMvB7CIqLmDtca4dD4gF7sfdGWffXTjwRe7M55pLg6eJ7c3c36u1aAH2gWJ6SJAocNxTiWLlLId437q2oCzsCwHhHlNcfhXA72IurZtIC5BYSQBlG5J6CvcuxHZ/wDQ8MtogG4xLXCNQW8j0A0rabhjWyMFrm92ebYX6N+IXiGvMludD3jl2HP2Vn0mtZwP6ORhw39YDFtz3cbch4zW8DUOaueeaUlXRrCCi7OXwvhRsKwnOSd4jQfGs/8ASOn9Uza6XE+YK/xrYvdrLfSEubA3Ooa2fS4v51lD7I2T3PKc9D8aCaItXSaWLNrSNRMakt02Ow2oKROlATSQMJqjiiLUJpomwiKGKMGiyjrQOiIGimhAp5pslBA0860yCnIpFDA9aIRQEUy86BE4oTRrQMakoNTtW17NCLS/E/M1iK2nALw7tF1nKKzy8AaOzd+Fee/SVanFgn61pInnGYET129RXrPC+zxe2HLhc2oETpyJ151zu1vZhGthLviUnwsNGVgNx009aMUtDtnPkSkqR5bwlWw6Zj3SG4MvesxZ7akeLuhEBiDEid62na2+uMwVtbaZbkAgRGW2gBb3CAunu8qwvE+ztzC3RmJa1PgdRInkCvI+VXF7QuFazZk3LoyO7DVV6CR4fSB767U090ctOOzJ+z4t27qNdQMghgdwjkIVuRt9mffNT4vCImNvI0frVV16QZk++R+NWG4Y9vC2bjL7Gay8D2gMzWm+K5h7wtcbjdtpUhgWtwUP92SNjzUSpHkxpSjqTRpgyeOak0X71q89vu0Z+7DZkWTMjRsh5AmdJ2NS28RiBYuWQzBWINzMSHYAQVmB4DA8zr1pYHi2UlLgC6kDXTTQwffOlNxrioy5FMuRpqNB1PQVx3kUtLR7ChgktaZS4JYS9xDCiIklm/whmE/EV18OeLDEuti+1tGe66AtmtZc5YwsNG45CSayljEvhb1vELBylgJ80hh6PXR7Vceu96qJcZAttVOQkE54uEEjX7NdkVsjx8zubfB6pge0t20y2sYLTOd3w+Yx5vaIzAea9do1rqf9RYcglGa6B7RtJcuKvkzIpCt5Eg615FwTiRXDuLNthcyuWvMQTHLINwSZ9OZrscQ4vi7HDQqILedyDIlwHBJgbIAF1ZpJJJgTWTwRbsFkaRrsN9IGEuX/ANHUXy+okWiQSNxCkt8SsV0uIceS1bd2tXxlUtBtXFBj7xEATzrB/Q92ad1fGG+basWtwgU3GAKlibjA5ASeWpjcVsu2SWBg7tsXCkrvmJlwQQXY+K4SREEnfrWcoQUqRcHKStninaPirX7rXHADOxYgTAnQATyAAFc4sp+rA8iSfnUeIYl43MxEa9AI61oOHdjcbcYA4d0ErJaFhSdSAd9J92ldWyRjds2n0YdmrYVMdnct+sVVIAXcrPU6T8a9O4fbmG+8VI5ezpXHwGEWzaSzaUhEEAGZiZljzJMmrnC79wXcuhU77ggiSCK4ZzcpWdCjUSS8wG9V3ah4ldJuNpAGnppXRwOCTICdZ135VFNsrhFDDMM6giRIB+JrOdsrM4XEDyJH+Eg/wrd28EimROsfIg1wO0+FzYbEJEnub5B156jy5VaiCkeEGo5qSaA61uajEUSGlbNI0DETQk071Ghp0JsKaTGmpxQIS0qcUqBgqKMihWnJoAJeVEpoJpK1IB4pUJNODpQBKDQzQlqQNKirCavW+Gdmu7w5OUs3d2ssb5iAXgctdPhXkoGoHU/jX0XhWhVHSBr7orLLwjObaLOCGVEWNlUegAqHjWDF5AswQZX37a1aRpos1Jbox4dmIx3CGytbuJKsMp5iD/M/CvFuF8Ze24BIdZgk7xMSGiY5wa+pNOY0r5V4vge5xV60BGS7cUDf2XIA+VdPx40mZZpNtM937IC3dsOjgMpKmD5ag+uvpXnfbLhv6PfKH2Zy9JsXswjTmrBh7gtdvsTxBggfbKNQNQQN48tPlUvbkJikzpBORspHnJg/ECtVyZlPsBwe1iM63Yfw2midcxUrmkbGbfzrmdpOxfc3Lpw7BmQuxtHVxbzEow8ssD4Uvo1vkkqMyXAM6spLF1zMDNttCAQRoZ8jXoNvHE3LneWS+YwbltM0BbaEqyxnSYGhAE1lJtMtOjxvAYNr+cmGddcpXwsvUEERpUuO4JmYXgWZG1bcsCNNDuROnURVu0ww99ZDKuZ+7JgZ7c+yY2I036CtDw3sm+LuXls43uW8Li2yllZCNWEHcNM6H2lqdUlOjuaxyxamr91ycHA45fEvhBPsRoIAAEe7WujjeJO1h7TnQownnBUxNX8f9EmMZlHf2GDE5mAcAaEglY5xEjqKDFfRHxBQFt4my6nfMzpB+KmfhW6a9nBL8Mz2J7YnBo9pwxtu2YR9RohiV5ggD92tVwvFXOJ3u5w8wIa5eYaWkJiVU6s52A/I1zh9DPENPHhv8x5HqmterdieyS8Owxt2yHusczufCHaIA5kINh7yedRJQu+wjKVV0Hg+xWEtoqKg8JkMyqzlt8xc6zOtdrD4VUECfPaa5tjjbG0XKICFsuAHkFbtwp7RAgjK2+mgoB2mskwAxPg08P155zyKwfhvNYtdlpnaDfCkzVwk7TWoHhaYVjBQwGRnOubXKFaf+ar8b4gblhmttkKltWOnsZgTlJjTkdQdxRQWaJulIJptWHscTuMqjuz7CE30a5kZiVVhB0EyRG8jbaIcLxK4M6FFxB70qTbNxTbU6CdP2oOwynXomijdlqrcQXNauL1Rx6qRQYe9KIxO6qfVQaTXRt1qNRVHzWp0HuH4UqJ0jTpp6aUE1ub2PSmmBpztRQCY0BpmNERpTEOaamFHNAxqeaGaWYUqHY4pUI2otqYrGBpgdKRoaBBqaQahBp6AsM0ppiaAiihtl/hyTetr9q5bHq6ivf7d3WOleCdm7ebF4cf3ts/usD/Cvb7JgzXLn2aCrO1bqQrrVe0wqwtKLMWida+efpD4cbfEb4Oha4binkVueNT6yvvBr6DQ15N9OoQNhHnxEXVI6oDbIPwJI9a6sMt6Mci2KPZq49rLdUEj64G8c2Xr5in7QkWC1634rFw+IDZC2zj7p5ioOxvFFIyn2lIn73mP5612eMqqhm0Npll13An2n8vMe81t2QZvgzjNYW37QxDoNoazcXPcBjlDGvRLSNahURrs3juTNtXm4j5wC5X6niMDIegFeX8AjDYxcx/V+I25MeJoWNdzlkCvVjjbxti5assrFWSbrWwpJDG3mCuTo8bx7Z2ms8nII80+lEqHRIhszNBjQEeWhBMQfKoPo1s3cRiO7TEmzdRC9hiuYSp8S7zGUk89Aag7aljcum5cR7hFpzkMqv1cinUmJJMHmKPsffezdtXkgsCXTlLLM2yejrI+Jq6/kak09me/cKv3iuW/bCXFiWQ5rT/eQ6ETzUgEee9XWNc7gXG7OLsLesmVbcGMynmjgbMOldAmud8lor8SxwtIGImWA9oLuCdzpyj4iqmD44LjMBbZQodiWgEC2QDK7zrtXQZVaJAMEESJgjYjzHWjLUJgZ8ccmMtlcp8OpA+uEiIgic8H7pNEOOqSoFlpYAiYB9tbYBkaHUx+yeld4tUN24QpME6EwNSfIa707FRxLvGgLaXe6hWW4SpHizKUCiRtIZtCOXKKr8WxwYhWWbZAaArZnDW7hZgwMACMp0bf3VaxXHytxbf6LiyGVmzLbUqII8JObQ6zVSx2hZndRhMWuTLq1tQGn7Pj1j41LstJFCzjAECd2y2gpIt5mjTuiBoBHidh/gnqKPA3FDsiWylxhcYxcIzupOvsjMpP1vlWm78czHx1+I61G7Lv4Z2nSY6TvUtlUcGzxYosFS4AUAhGUDw25Q+0ZXMRrHsnTSungsYLiyVysDqNTGuhkgbipi2bYyfIzUbKf5/n3Vm2VR8/8ZTJiLy9Lt0fAOwqoa6fa5MuOxI/vWPr4v41ylNdZaGopoWp50pjEwogaY7UymhgJBypyaY70iKQDgUshpTSigBs2lKaamFMQdCTTk0B2oBjqaKaAGiBoAKmG9PNBOtAM0HYsTjbB6MT6I1evJcE15J2EWcWukwjn5Afxr1G1bJP86Vx/I+yNIrY7Vi751eR+lcqwsCrtsVmmZyReVq8m+nXhs9xiQwgA2ipOu5cMo585+FeqWvWvHvpu4lba9YsKwLWlc3FH1Tc7srJ6wu3IR1rq+P9jny8Gfs4Mtat3cNpcWCBzIP1fMg8vM13OGdoUvIbbjLc1DIduhI8t6wFnGOqZVMAMGB2II2+ddC5jkvQzkpeX64BgkczFdlGBaeUbumGYAzbJ5qPqH3VuuyTg4S2oVCSbwVWEr3oF7u8+moBDf6Y2rA4W53wykjOPEGHlsfzqW3xm/ZsnJAzMM0icjodSPfoD/zUyVjs1Ham4l7u0vFFdLLtcIMKDcCqoB6SpPwFZXsziQwNhjBGqmddCT4T1B1FchcUzXO8uMXJ3MiY8pEDnyqNgVYMjazIidI2ppVsKzaYPiWJ4bjnyMAHg5TJtXFIBmNI1kAjVdtefrvZztdYxcLPd3o/7TESfNDs4+fUV5WmMt8Rw6rouItCR1DCJ1+w2mvI1Tw7BlO/4EMD5bMCNx0qZRTKTo+gQKrcTxRt2y4g5Spg8xmGYA8jEwdpivPeznbi5aATEzdTlcGt1f2h/aDz9r31tL/G1a0l2wVuqWykgnQZWYzAJUggaEc6wcHE0TTBw3GmzLbdPEWyll0Wc4Q6HaJLQTtHWBDiuOMA2W0dA/i1OUgeGVjUzMrOkVJiOMuoWbRllB+tE/rDE5dvAu8f9wTFVzxi81pmFooQwUA5idmnwxPIR1zjapsdEtzjDZJ7qT3hQwdJUeIgxqM0gdZHnXKu9oXykiww8JIk88rMsgAncZY5NA5zVu3xC9lZTZylEJ0kgsDEooUSvtGB086o3uJX82VQWGfR2VhK5ozQoiND0PlzrOVejSKKXHbuW/bY3FBNwDKUzK/6u1uTspY+cTPmKePN422a8q4dsjEZVB2cAHKDoSCRM7dNat38VcAD3rQIGQl5dcrEN4iFAgrGp31HShxRdlVgrEtbQ5fG5JYt3iFm2AWNNPa2MRRqHpFwvF3i1pu7U2YTLeCgMxK5TOvMkzpy+Fdw4g+dcbDXnlf1TKkkLJumIPh8LaAbHXr5V0zePOBWU3uaRjseRduT/X8QerKfW2hrhTWi+kEf11iOaWz/AKcp/wDWs2DXdHeKJ4JDTJTA0w0pjCBplahfehpismJ1pGgmiJpDscGizVHFKKKCwopjRTQUAEDTU00zHSgLFSmhpUySUGhBpCkaRRpvo9xKrjBmgZrbKv7RKsPkpr1NCQRXhFswZGhBkEbyNQfWtDZ7ZYpQBmRo5spn4kETWGXFqdoqMqR7LbY1YRj5RXj9v6Q8WNls/uv/AL6M/SPjB9Wz+6/+6oWBkOX4bL6QO1xwloW7RHf3Bod+7TYvHNjqFHvPKvEr0uxJkliSZJJnckk6k+Zrqca4hdxV1r1xlzMFEAGAFAACgnQc/eTVFbJU6MNiNq7MajCNHPOE5O6KqYckAjn/AA3pkVgY5xVxEZVy5tJnbnEfhUL2idz8qvUiPFL0JcQQREqRtVrD4sMxVh7e4+9yI9PwqC/bL6kjToKHuDoZ28qNSDxy9E2Iv3Fm30931oIqC7inIgnmfxE/Opr5Z2LEiTE6dBAqubPKaLQ/HI7nA0FvDtfTW4pk+4aFfipJ9OlWbGMBPeWz4WjOPssYGb8AeWx5VxsFiHtBgrCHEEET6etQ2lZTKtGkbaEeYpJ+xvG9qRsw01LgsXcsv3lp2R9sy7kbwwOjDyINY+1xC6ogMIHUA0X9KXvtj91fyp2haJHsPB+349nFKE/vUDFPe6alPeJHurZ2rwZQysCrAQQQQR5Eb182/wBK3o9sfuirfCO1WLw2bubsBtSpRSs/aCkaN5jfnWM8SfBcdS6PoVmj3VA9zqK8Sf6QuIH+2T/Kt/lUb9u+IH+3X/Kt/lWLwP2aqX4e1XhOk1WtWcogma8abtxxA/8AkD/Ktf7ab/rbiH/yP/qs/wAVqf8AO/ZSnXR7JdBGtVHJ6TXkbdsuIH/yT/l2f9lBf7VY5wQ2JaDpottT6qoIo/zfo1l/C126xSXMW2TZFVD+0JJ9Jj4Vm6IaUxrpSpUSxA0dRA0YOlMLE9DSzU1Ag1ohQinFJlIc0001NNMAwaVIUqQDdaGKI86amgB50VCKKgSHXejLVGtSXP4UihU4oTtTigY9KkvKkN6AHpA04oRQA7nSo6PlUQoJDpjRUJoAZjQikaQpksImhzUqGhDYS0qQ2pqBCJpA01IUwHFETTUxpAMaVKmFMAppA01IUAFTU1PQA0UgaQpqAE1PTNTpQA9PNLmKT0hj01PQ0Az/2Q==",
            ),
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
            if (
                _identity_equals(player.identity, IdentityDTO.XERIFE)
                and player.is_alive
            ):
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
