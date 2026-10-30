import numpy as np
import pytest
import torch

from app.bot.value_eval import NumpyValueNet
from app.sim.dataset import N_FEATURES
from app.sim.runner import build_agents, play_game
from app.sim.train_value import ValueNet, load_model, save_model, train


@pytest.fixture
def net_path(tmp_path):
    torch.manual_seed(0)
    path = tmp_path / "net.pt"
    save_model(ValueNet(), path, {})
    return path


def test_rede_em_numpy_igual_a_do_torch(net_path):
    x = np.random.default_rng(0).random(N_FEATURES).astype(np.float32)
    with torch.no_grad():
        expected = load_model(net_path)(torch.from_numpy(x[None]))[0].item()
    assert NumpyValueNet.load(net_path).logit(x) == pytest.approx(expected, abs=1e-5)


def test_treino_aprende_um_sinal_simples():
    rng = np.random.default_rng(0)
    x = rng.random((2000, N_FEATURES)).astype(np.float32)
    y = (x[:, 0] > 0.5).astype(np.float32)
    data = {"X": x, "y": y, "groups": np.arange(2000) // 10, "players": np.full(2000, 5)}
    _, metrics, _ = train(data, log=lambda *_: None)
    assert metrics.auc > 0.95


def test_agente_com_rede_de_valor_joga_partida_valida(net_path):
    spec = f"bayes:medio:n=4:value={net_path.as_posix()}"
    result = play_game(1, 5, build_agents([spec] * 5, 1))
    assert not result.timed_out
