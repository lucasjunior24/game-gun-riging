"""Treina a rede de valor V(observacao) ~ P(meu time vence | observacao).

    python -m app.sim.train_value results/data/gen1.npz --out app/models/value_net_v1.pt
    python -m app.sim.train_value results/data/gen1.npz results/data/gen2.npz   # versao seguinte

Substitui app/training.py, que imitava uma regra fixa: aqui o rotulo e o resultado real.
"""

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import torch

from app.sim.dataset import N_FEATURES, load
from app.sim.stats import auc

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
CALIBRATION_BINS = 10


class ValueNet(torch.nn.Module):
    def __init__(self, n_in: int = N_FEATURES):
        super().__init__()
        self.n_in = n_in
        self.net = torch.nn.Sequential(
            torch.nn.Linear(n_in, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)  # logit; sigmoid da a probabilidade


@dataclass
class TrainConfig:
    epochs: int = 60
    batch_size: int = 512
    lr: float = 1e-3
    weight_decay: float = 1e-4  # regularizacao L2
    patience: int = 6  # parada antecipada: epocas sem melhorar a validacao
    val_fraction: float = 0.2
    seed: int = 0


@dataclass
class Metrics:
    loss: float  # entropia cruzada binaria
    auc: float
    ece: float  # erro de calibracao esperado
    calibration: list[tuple[float, float, int]] = field(default_factory=list)  # (previsto, real, n)


def group_split(
    groups: np.ndarray, val_fraction: float, seed: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Separa por partida, nao por linha. Linhas da mesma partida sao quase iguais: se
    caissem em treino e validacao ao mesmo tempo, a validacao ficaria falsamente boa."""
    unique = np.unique(groups)
    rng = np.random.default_rng(seed)
    rng.shuffle(unique)
    n_val = max(1, int(round(len(unique) * val_fraction)))
    val_groups = unique[:n_val]
    is_val = np.isin(groups, val_groups)
    return np.flatnonzero(~is_val), np.flatnonzero(is_val)


def calibration(probs: np.ndarray, labels: np.ndarray, bins: int = CALIBRATION_BINS):
    """Diagrama de confiabilidade: se a rede diz 70%, o time vence ~70% dessas vezes?"""
    edges = np.linspace(0, 1, bins + 1)
    which = np.clip(np.digitize(probs, edges) - 1, 0, bins - 1)
    table = []
    ece = 0.0
    for b in range(bins):
        mask = which == b
        n = int(mask.sum())
        if n == 0:
            continue
        predicted, actual = float(probs[mask].mean()), float(labels[mask].mean())
        table.append((predicted, actual, n))
        ece += n / len(probs) * abs(predicted - actual)
    return table, ece


def evaluate(model: ValueNet, x: torch.Tensor, y: torch.Tensor) -> Metrics:
    model.eval()
    with torch.no_grad():
        logits = model(x)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, y).item()
        probs = torch.sigmoid(logits).numpy()
    labels = y.numpy()
    table, ece = calibration(probs, labels)
    return Metrics(loss, auc(probs.tolist(), labels.tolist()), ece, table)


def train(
    data: dict[str, np.ndarray], config: TrainConfig | None = None, log=print
) -> tuple[ValueNet, Metrics, list[dict]]:
    config = config or TrainConfig()
    torch.manual_seed(config.seed)
    train_idx, val_idx = group_split(data["groups"], config.val_fraction, config.seed)
    x = torch.from_numpy(data["X"].astype(np.float32))
    y = torch.from_numpy(data["y"].astype(np.float32))
    x_train, y_train, x_val, y_val = x[train_idx], y[train_idx], x[val_idx], y[val_idx]

    model = ValueNet(x.shape[1])
    loss_fn = torch.nn.BCEWithLogitsLoss()  # entropia cruzada binaria
    opt = torch.optim.Adam(model.parameters(), lr=config.lr, weight_decay=config.weight_decay)
    generator = torch.Generator().manual_seed(config.seed)

    best_loss, best_state, stale = float("inf"), None, 0
    history = []
    for epoch in range(1, config.epochs + 1):
        model.train()
        order = torch.randperm(len(x_train), generator=generator)
        total = 0.0
        for start in range(0, len(order), config.batch_size):
            batch = order[start : start + config.batch_size]
            opt.zero_grad()
            loss = loss_fn(model(x_train[batch]), y_train[batch])
            loss.backward()
            opt.step()
            total += loss.item() * len(batch)
        val = evaluate(model, x_val, y_val)
        history.append({"epoch": epoch, "train_loss": total / len(x_train), "val_loss": val.loss})
        log(f"epoca {epoch:3d}: treino {total / len(x_train):.4f}  validacao {val.loss:.4f}  AUC {val.auc:.3f}")
        if val.loss < best_loss - 1e-4:
            best_loss, stale = val.loss, 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
            if stale >= config.patience:
                log(f"parada antecipada: {config.patience} epocas sem melhorar")
                break

    model.load_state_dict(best_state)
    return model, evaluate(model, x_val, y_val), history


def save_model(model: ValueNet, path: str | Path, meta: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "n_in": model.n_in, "meta": meta}, path)


def load_model(path: str | Path) -> ValueNet:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    model = ValueNet(checkpoint["n_in"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model


def next_model_path() -> Path:
    versions = [
        int(m.group(1))
        for p in MODELS_DIR.glob("value_net_v*.pt")
        if (m := re.fullmatch(r"value_net_v(\d+)\.pt", p.name))
    ]
    return MODELS_DIR / f"value_net_v{max(versions, default=0) + 1}.pt"


def render_metrics(metrics: Metrics, baseline: float) -> str:
    lines = [
        f"validacao: BCE {metrics.loss:.4f} (prever sempre a media: {baseline:.4f}), "
        f"AUC {metrics.auc:.3f}, ECE {metrics.ece:.3f}",
        "calibracao (previsto -> real, n):",
    ]
    for predicted, actual, n in metrics.calibration:
        lines.append(f"  {predicted:5.2f} -> {actual:5.2f}  ({n})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("data", nargs="+", help="arquivos .npz de app.sim.dataset")
    parser.add_argument("--out", help="padrao: app/models/value_net_v{n+1}.pt")
    defaults = TrainConfig()
    for name, value in asdict(defaults).items():
        parser.add_argument(f"--{name.replace('_', '-')}", type=type(value), default=value)
    args = parser.parse_args(argv)

    config = TrainConfig(**{name: getattr(args, name) for name in asdict(defaults)})
    data = load(args.data)
    print(f"{len(data['y'])} posicoes, {len(np.unique(data['groups']))} partidas, "
          f"{data['y'].mean():.1%} de rotulos positivos")
    model, metrics, history = train(data, config)

    _, val_idx = group_split(data["groups"], config.val_fraction, config.seed)
    p = float(data["y"][val_idx].mean())
    baseline = -(p * np.log(p) + (1 - p) * np.log(1 - p))
    print(render_metrics(metrics, baseline))

    out = Path(args.out) if args.out else next_model_path()
    meta = {
        "data": [str(Path(d)) for d in args.data],
        "config": asdict(config),
        "val_loss": metrics.loss,
        "val_auc": metrics.auc,
        "val_ece": metrics.ece,
        "epochs_run": len(history),
        "created": time.strftime("%Y-%m-%d %H:%M"),
    }
    save_model(model, out, meta)
    print(f"modelo salvo em {out}")
    print(json.dumps({k: v for k, v in meta.items() if k != "config"}, indent=2))


if __name__ == "__main__":
    main()
