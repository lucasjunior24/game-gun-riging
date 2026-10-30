from app.dtos.character import IdentityDTO, TeamDTO
from app.engine.events import EventType, GameEvent
from app.engine.roles import team_for
from app.sim.runner import GameResult, build_agents, causes_of_death, play_game


def agents(players, spec="heuristic", seed=0):
    return build_agents([spec] * players, seed)


def test_mesma_semente_mesma_partida():
    a = play_game(42, 5, agents(5, "bayes:medio:n=4", 42))
    b = play_game(42, 5, agents(5, "bayes:medio:n=4", 42))
    assert a == b


def test_sementes_diferentes_dao_partidas_diferentes():
    results = {repr(play_game(s, 5, agents(5, seed=s)).to_dict()) for s in range(10)}
    assert len(results) > 1


def test_partidas_terminam_sem_timeout():
    results = [play_game(s, n, agents(n, seed=s)) for s in range(300) for n in (4, 5, 8)]
    assert not any(r.timed_out for r in results)
    assert all(r.winner is not None for r in results)


def test_bayes_termina_em_varios_tamanhos():
    for n in (4, 6, 8):
        result = play_game(n, n, agents(n, "bayes:medio:n=4", n))
        assert not result.timed_out


def test_todos_os_times_vencem_alguma_vez():
    # sanidade: se o Renegado nunca vence, ha bug (era o bug 2 do diagnostico)
    winners = {play_game(s, 4, agents(4, seed=s)).winner for s in range(2000)}
    assert len(winners) == 3


def test_resultado_vai_e_volta_em_json():
    result = play_game(7, 5, agents(5, seed=7))
    assert GameResult.from_dict(result.to_dict()) == result


def test_toda_morte_tem_causa():
    result = play_game(3, 6, agents(6, seed=3))
    assert result.deaths
    assert all(cause in ("TIRO", "INDIOS", "DINAMITE", "GATLING") for _, cause in result.deaths)


def test_causa_da_morte_e_o_evento_que_causou_o_dano():
    def ev(event_type, target=None):
        return GameEvent(type=event_type, round_number=1, turn_number=1, target_seat=target)

    events = [
        ev(EventType.SHOT, 1),
        ev(EventType.DAMAGE, 1),
        ev(EventType.DEATH, 1),
        ev(EventType.INDIAN_ATTACK),
        ev(EventType.DAMAGE, 2),
        ev(EventType.DEATH, 2),
        ev(EventType.DAMAGE, 3),
        ev(EventType.DEATH, 3),
        ev(EventType.GATLING),
        ev(EventType.DAMAGE, 4),
        ev(EventType.DEATH, 4),
    ]
    assert causes_of_death(events) == [(1, "TIRO"), (2, "INDIOS"), (3, "INDIOS"), (4, "GATLING")]


def test_vitoria_e_do_time_do_assento():
    result = play_game(11, 5, agents(5, seed=11))
    for seat, role in enumerate(result.roles):
        assert result.won(seat) == (team_for(role) is result.winner)


def test_com_dois_renegados_so_o_sobrevivente_vence():
    result = next(
        r for s in range(3000)
        if (r := play_game(s, 8, agents(8, seed=s))).winner is TeamDTO.RENEGADO
    )
    renegades = [seat for seat, role in enumerate(result.roles) if role is IdentityDTO.RENEGADO]
    assert sum(result.won(seat) for seat in renegades) == 1
