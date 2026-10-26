import math

import pytest

from app.bot.belief import infer
from app.bot.likelihood import FixedTable, SoftmaxLikelihood
from app.engine.events import EventType
from app.engine.view import build_observation

from bot_helpers import ASSISTENTE, FORA_DA_LEI, RENEGADO, XERIFE, add_event, new_state

# 5 jogadores, bot Fora da lei no assento 2. Ocultos: A = 3, B = 4, C = 1
A, B, C = 3, 4, 1
DOC_TABLE = FixedTable({FORA_DA_LEI: 0.6, RENEGADO: 0.15, ASSISTENTE: 0.02})


def test_exemplo_do_documento():
    """Reproduz a tabela da secao 3.2: A atira no Xerife podendo atirar em outro."""
    state = new_state(5)
    add_event(state, EventType.SHOT, actor=A, target=0, options=[0, B])

    belief = infer(build_observation(state, 2), DOC_TABLE)

    assert belief.marginal(A)[FORA_DA_LEI] == pytest.approx(0.779, abs=1e-3)
    assert belief.marginal(A)[RENEGADO] == pytest.approx(0.195, abs=1e-3)
    assert belief.marginal(B)[ASSISTENTE] == pytest.approx(0.487, abs=1e-3)  # B nao agiu!
    assert belief.marginal(B)[RENEGADO] == pytest.approx(0.403, abs=1e-3)
    assert belief.marginal(C)[FORA_DA_LEI] == pytest.approx(0.110, abs=1e-3)


def test_acao_forcada_nao_muda_crenca():
    state = new_state(5)
    add_event(state, EventType.SHOT, actor=A, target=0, options=[0])  # unico alvo valido

    probs = infer(build_observation(state, 2)).probabilities()

    assert probs == pytest.approx([1 / 6] * 6)


def test_propria_jogada_nao_muda_crenca():
    state = new_state(5)
    add_event(state, EventType.SHOT, actor=2, target=0, options=[0, 4])

    probs = infer(build_observation(state, 2)).probabilities()

    assert probs == pytest.approx([1 / 6] * 6)


def test_ruido_impede_probabilidade_zero():
    """Um Assistente que atira no Xerife varias vezes continua possivel."""
    state = new_state(5)
    for _ in range(6):
        add_event(state, EventType.SHOT, actor=4, target=0, options=[0, 3])

    belief = infer(build_observation(state, 2))

    assert all(math.isfinite(x) for x in belief.log_w)
    assert belief.marginal(4)[ASSISTENTE] > 0
    real = next(i for i, w in enumerate(belief.worlds) if w[4] is ASSISTENTE and w[1] is RENEGADO)
    assert belief.probabilities()[real] > 0


def test_tiro_no_xerife_aumenta_fora_da_lei():
    state = new_state(5)
    add_event(state, EventType.SHOT, actor=3, target=0, options=[0, 2])

    marginal = infer(build_observation(state, 4)).marginal(3)

    assert marginal[FORA_DA_LEI] > 2 / 3  # prior: 2 FL entre 3 ocultos


def test_cerveja_no_xerife_aumenta_assistente():
    state = new_state(5)
    state.players[0].life -= 2
    add_event(state, EventType.BEER, actor=4, target=0, options=[0, 1, 2, 3, 4])

    marginal = infer(build_observation(state, 0)).marginal(4)

    assert marginal[ASSISTENTE] > 0.25  # prior: 1 Assistente entre 4 ocultos
    assert marginal[FORA_DA_LEI] < 0.5


def test_tiro_em_quem_atirou_no_xerife_aumenta_assistente():
    state = new_state(5)
    add_event(state, EventType.SHOT, actor=3, target=0, options=[0, 2])
    add_event(state, EventType.SHOT, actor=4, target=3, options=[3, 0])

    marginal = infer(build_observation(state, 0)).marginal(4)

    assert marginal[ASSISTENTE] > 0.25


def test_soma_das_probabilidades_e_1():
    state = new_state(8)
    add_event(state, EventType.SHOT, actor=3, target=0, options=[0, 2])
    add_event(state, EventType.BEER, actor=5, target=0, options=list(range(8)))
    for viewer in range(8):
        belief = infer(build_observation(state, viewer))
        assert sum(belief.probabilities()) == pytest.approx(1.0)
        for seat in range(8):
            assert sum(belief.marginal(seat).values()) == pytest.approx(1.0)


def test_xerife_tem_marginal_certa():
    belief = infer(build_observation(new_state(5), 3), SoftmaxLikelihood())
    assert belief.marginal(0) == pytest.approx({XERIFE: 1.0})
