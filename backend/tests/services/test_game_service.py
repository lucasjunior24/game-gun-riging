from app.dtos.character import IdentityDTO, TeamDTO
from app.dtos.game_state import (
    CreateAuthoritativeGameDTO,
    ExecuteShotsCommandDTO,
    ShootDistanceCommandDTO,
)
from app.dtos.dice import UserBulletsDTO
from app.services.game_service import GameService


def test_public_state_does_not_expose_private_identity_or_belief():
    service = GameService()

    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))

    assert state.players[0].revealed_identity == IdentityDTO.XERIFE
    assert state.players[1].revealed_identity is None
    assert not hasattr(state.players[1], "papel_probability")
    assert not hasattr(state.players[1], "identity")
    assert not hasattr(state.players[1], "team")


def test_execute_shots_updates_life_history_and_turn():
    service = GameService()
    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))
    target = state.players[1]

    updated = service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=state.current_player.user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[
                        UserBulletsDTO(user_name=target.user_name, shots=2)
                    ],
                )
            ],
        ),
    )

    updated_target = next(
        player for player in updated.players if player.user_name == target.user_name
    )
    internal_state = service._games[state.game_id]

    assert updated_target.bullet == target.bullet - 2
    assert internal_state.action_history[0].actor_user_name == "Lucas"
    assert internal_state.action_history[0].target_user_name == target.user_name
    assert updated.turn_number == 2


def test_history_updates_belief_inside_backend_only():
    service = GameService()
    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))
    outlaw = state.players[1]

    service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=outlaw.user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name="Lucas", shots=1)],
                )
            ],
        ),
    )

    internal_state = service._games[state.game_id]
    internal_outlaw = next(
        player for player in internal_state.players if player.user_name == outlaw.user_name
    )
    public_outlaw = next(
        player
        for player in service.get_state(state.game_id).players
        if player.user_name == outlaw.user_name
    )

    assert internal_outlaw.papel_probability.fora_da_lei > internal_outlaw.papel_probability.assistente
    assert internal_outlaw.papel_probability.xerife == 0
    assert not hasattr(public_outlaw, "papel_probability")


def test_winner_is_resolved_when_sheriff_dies():
    service = GameService()
    state = service.create_game(CreateAuthoritativeGameDTO(player_name="Lucas"))
    actor = state.players[1]

    updated = service.execute_shots(
        state.game_id,
        ExecuteShotsCommandDTO(
            actor_user_id=actor.user_id,
            shots_by_distance=[
                ShootDistanceCommandDTO(
                    distance="1",
                    user_bullets=[UserBulletsDTO(user_name="Lucas", shots=99)],
                )
            ],
        ),
    )

    assert updated.status == "Done"
    assert updated.winner == TeamDTO.FORA_DA_LEI
