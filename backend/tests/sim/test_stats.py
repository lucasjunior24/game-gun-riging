import math

import pytest

from app.sim.stats import auc, binomial_two_sided, mcnemar, wilson


def test_wilson_valores_conhecidos():
    lo, hi = wilson(50, 100)
    assert lo == pytest.approx(0.404, abs=1e-3)
    assert hi == pytest.approx(0.596, abs=1e-3)


def test_wilson_nos_extremos_fica_entre_0_e_1():
    lo, hi = wilson(0, 20)
    assert lo == pytest.approx(0.0, abs=1e-12)
    assert hi == pytest.approx(0.161, abs=1e-3)
    assert wilson(0, 0) == (0.0, 1.0)


def test_margem_e_cerca_de_1_sobre_raiz_de_n():
    lo, hi = wilson(1000, 2000)
    assert (hi - lo) / 2 == pytest.approx(1 / math.sqrt(2000), abs=0.001)


def test_mcnemar_exato_com_poucos_pares():
    _, p = mcnemar(10, 2)
    assert p == pytest.approx(158 / 4096)  # 2 * P(X <= 2), X ~ Binomial(12, 1/2)


def test_mcnemar_qui_quadrado_com_muitos_pares():
    statistic, p = mcnemar(40, 20)
    assert statistic == pytest.approx(19**2 / 60)
    assert p == pytest.approx(0.01417, abs=1e-4)  # qui-quadrado 6,017 com 1 grau


def test_mcnemar_sem_diferenca():
    assert mcnemar(0, 0) == (0.0, 1.0)
    assert mcnemar(30, 30)[1] > 0.8


def test_teste_do_sinal_e_simetrico():
    assert binomial_two_sided(3, 10) == pytest.approx(binomial_two_sided(7, 10))
    assert binomial_two_sided(5, 10) == 1.0


def test_auc():
    assert auc([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]) == 1.0
    assert auc([0.9, 0.8, 0.2, 0.1], [0, 0, 1, 1]) == 0.0
    assert auc([0.5, 0.5, 0.5, 0.5], [0, 1, 0, 1]) == 0.5
