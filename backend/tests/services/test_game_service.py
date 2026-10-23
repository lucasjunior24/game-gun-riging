from app.dtos.character import IdentityDTO, TeamDTO
from app.dtos.game_state import (
    CreateAuthoritativeGameDTO,
    ExecuteShotsCommandDTO,
    ShootDistanceCommandDTO,
)
from app.dtos.dice import UserBulletsDTO
from app.engine.dice import DiceFace
from app.services.game_service import GameService
from app.services.history_adapter import events_to_history

from conftest import force_dice


def test_public_state_does_not_expose_private_identity_or_belief():
    service = GameService()

    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))

    assert state.players[0].revealed_identity == IdentityDTO.XERIFE.value
    assert state.players[1].revealed_identity is None
    assert not hasattr(state.players[1], "papel_probability")
    assert not hasattr(state.players[1], "identity")
    assert not hasattr(state.players[1], "team")


def test_execute_shots_updates_life_history_and_turn():
    service = GameService()
    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))
    target = state.players[1]

    force_dice(
        service,
        state.game_id,
        [DiceFace.SHOT_1, DiceFace.SHOT_1, DiceFace.ARROW, DiceFace.ARROW, DiceFace.ARROW],
    )
    updated = service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.current_player.user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name=target.user_name, shots=2)],
                )
            ],
        ),
    )

    updated_target = next(
        player for player in updated.players if player.user_name == target.user_name
    )
    internal_state = service._games[state.game_id]

    assert updated_target.bullet == target.bullet - 2
    history = events_to_history(internal_state)
    shot_events = [a for a in history if a.action_type == "TIRO"]
    assert any(a.target_user_name == target.user_name for a in shot_events)
    assert updated.turn_number == 2


def test_history_does_not_leak_hidden_identities():
    service = GameService()
    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))
    outlaw_seat = state.players[1].user_name

    service._games[state.game_id].turn.seat = 1  # e a vez do jogador 1
    force_dice(
        service,
        state.game_id,
        [DiceFace.SHOT_1, DiceFace.ARROW, DiceFace.ARROW, DiceFace.ARROW, DiceFace.ARROW],
    )
    service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.players[1].user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name="Lucas", shots=1)],
                )
            ],
        ),
    )

    internal_state = service._games[state.game_id]
    history = events_to_history(internal_state)
    shot = next(a for a in history if a.actor_user_name == outlaw_seat)

    # O atirador (papel oculto) nao aparece com identidade no historico.
    assert shot.actor_identity is None
    # O alvo e o Xerife, que e sempre publico.
    assert shot.target_identity == IdentityDTO.XERIFE.value

    public_outlaw = next(
        player
        for player in service.get_state(state.game_id).players
        if player.user_name == outlaw_seat
    )
    assert not hasattr(public_outlaw, "papel_probability")


def test_winner_is_resolved_when_sheriff_dies():
    service = GameService()
    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))
    sheriff_seat = state.players[0].user_name
    assert sheriff_seat == "Lucas"

    internal_state = service._games[state.game_id]
    internal_state.turn.seat = 1  # e a vez do jogador 1
    internal_state.players[0].life = 1  # deixa o Xerife a um tiro da morte

    force_dice(
        service,
        state.game_id,
        [DiceFace.SHOT_1, DiceFace.ARROW, DiceFace.ARROW, DiceFace.ARROW, DiceFace.ARROW],
    )
    updated = service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.players[1].user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name="Lucas", shots=1)],
                )
            ],
        ),
    )

    assert updated.status == "Done"
    assert updated.winner == TeamDTO.FORA_DA_LEI.value
