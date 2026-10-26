from app.bot.agent import BayesAgent
from app.bot.resolution import candidate_targets, exhaustive_plans, plan_count
from app.dtos.game_state import DifficultyDTO
from app.engine.dice import DiceFace
from app.engine.events import EventType
from app.engine.rules import GameEngine
from app.engine.view import build_observation

from bot_helpers import add_event, kill, new_state, set_turn

ONE, TWO, BEER = DiceFace.SHOT_1, DiceFace.SHOT_2, DiceFace.BEER
ARROW, GATLING, DYNAMITE = DiceFace.ARROW, DiceFace.GATLING, DiceFace.DYNAMITE


def decide(state, seat):
    agent = BayesAgent(difficulty=DifficultyDTO.DIFICIL, seed=1)
    return agent.choose_assignments(build_observation(state, seat))


def targets(decision):
    return [a.target_seat for a in decision.action]


def test_fora_da_lei_atira_no_xerife_quando_alcanca():
    state = new_state(5)  # FL no assento 2: o "2" alcanca 0 (Xerife) e 4
    set_turn(state, 2, [TWO, ARROW, ARROW, GATLING, DYNAMITE])
    assert targets(decide(state, 2)) == [0]


def test_renegado_nao_mata_xerife_com_outros_vivos():
    state = new_state(5)  # Renegado no assento 1: o "1" alcanca 0 (Xerife) e 2
    state.players[0].life = 1
    set_turn(state, 1, [ONE, ARROW, ARROW, GATLING, DYNAMITE])
    assert targets(decide(state, 1)) == [2]


def test_renegado_cura_xerife_quase_morto():
    state = new_state(5)
    state.players[0].life = 1
    state.players[1].life = 6
    set_turn(state, 1, [BEER, ARROW, ARROW, GATLING, DYNAMITE])
    assert targets(decide(state, 1)) == [0]


def test_renegado_ataca_xerife_quando_so_restam_os_dois():
    state = new_state(5)
    for seat in (2, 3, 4):
        kill(state, seat)
    state.players[0].life = 3
    state.players[1].life = 6
    set_turn(state, 1, [ONE, BEER, ARROW, GATLING, DYNAMITE])
    decision = decide(state, 1)
    assert targets(decision) == [0, 1]  # atira no Xerife e cura a si mesmo, nunca ele


def test_dois_tiros_no_mesmo_alvo_quando_matam():
    state = new_state(5)  # Xerife no assento 0: o "1" alcanca 1 e 4
    add_event(state, EventType.SHOT, actor=1, target=0, options=[0, 2])
    add_event(state, EventType.SHOT, actor=4, target=0, options=[0, 3])
    state.players[1].life = 2
    set_turn(state, 0, [ONE, ONE, ARROW, GATLING, DYNAMITE])
    assert targets(decide(state, 0)) == [1, 1]


def test_assistente_evita_alvo_provavelmente_aliado():
    state = new_state(7)  # Assistentes nos assentos 4 e 6; o "2" do 4 alcanca 2 e 6
    state.players[0].life -= 3
    add_event(state, EventType.BEER, actor=6, target=0, options=list(range(7)))
    add_event(state, EventType.BEER, actor=6, target=0, options=list(range(7)))
    add_event(state, EventType.SHOT, actor=2, target=0, options=[0, 4])
    set_turn(state, 4, [TWO, ARROW, ARROW, GATLING, DYNAMITE])
    assert targets(decide(state, 4)) == [2]


def test_sem_dados_com_alvo_devolve_plano_vazio():
    state = new_state(5)
    set_turn(state, 2, [ARROW, ARROW, GATLING, GATLING, DYNAMITE])
    decision = decide(state, 2)
    assert decision.action == []
    assert decision.reason


def test_plano_e_aceito_pelo_motor():
    engine = GameEngine()
    state = new_state(8)
    for p in state.players:
        p.life = 2
    set_turn(state, 3, [ONE, ONE, TWO, BEER, BEER])
    decision = decide(state, 3)
    result = engine.resolve(state, 3, decision.action)
    assert result.turn.seat != 3 or result.status.value == "Done"


def test_cerveja_testa_so_feridos_e_um_desperdicio():
    state = new_state(8)
    state.players[2].life -= 1
    state.players[5].life -= 1
    set_turn(state, 3, [BEER, ARROW, ARROW, ARROW, DYNAMITE])
    assert candidate_targets(state, 3, BEER) == [2, 3, 5]


def test_dados_iguais_nao_geram_planos_repetidos():
    engine = GameEngine()
    state = new_state(8)
    for p in state.players:
        p.life -= 1
    set_turn(state, 3, [BEER, BEER, ARROW, ARROW, DYNAMITE])
    plans = exhaustive_plans(engine, state, 3, lambda s: 0.0)
    assert plan_count(engine, state, 3) == 36  # C(8 + 2 - 1, 2), e nao 8 * 8
    assert len(plans) == 36
    assert len({tuple(sorted(a.target_seat for a in plan)) for plan, _ in plans}) == 36
