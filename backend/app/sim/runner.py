import math
import random
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from functools import lru_cache

from app.bot.agent import Agent
from app.bot.belief import infer
from app.bot.likelihood import LikelihoodModel
from app.dtos.character import IdentityDTO, TeamDTO
from app.engine.events import EventType, GameEvent
from app.engine.roles import team_for
from app.engine.rules import GameEngine, PlayerSpec
from app.engine.state import EngineState, GameStatus
from app.engine.view import build_observation
from app.services.bot_turn_runner import BotTurnRunner

MAX_TURNS = 400
LIFE = 8  # todos os personagens padrao do GameService tem 8 de vida

# Causas de morte: o evento que causou o ultimo dano
CAUSES = {
    EventType.SHOT: "TIRO",
    EventType.INDIAN_ATTACK: "INDIOS",
    EventType.DYNAMITE_EXPLODED: "DINAMITE",
    EventType.GATLING: "GATLING",
}

OnTurn = Callable[[EngineState], None]


@dataclass
class GameResult:
    seed: int
    players: int
    winner: TeamDTO | None
    turns: int
    rounds: int
    roles: list[IdentityDTO]
    agent_names: list[str]
    deaths: list[tuple[int, str]]  # (assento, causa: TIRO, INDIOS, DINAMITE, GATLING)
    timed_out: bool
    shots: list[int] = field(default_factory=list)  # tiros dados por assento
    friendly_shots: list[int] = field(default_factory=list)  # tiros em aliado real
    belief_loss: float = 0.0  # soma de -log p(papel real), se medido
    belief_count: int = 0

    def won(self, seat: int) -> bool:
        if self.winner is None or team_for(self.roles[seat]) is not self.winner:
            return False
        if self.winner is TeamDTO.RENEGADO:  # com 8 jogadores ha dois: so o que sobrou vence
            return all(dead != seat for dead, _ in self.deaths)
        return True

    def to_dict(self) -> dict:
        data = asdict(self)
        data["winner"] = self.winner.value if self.winner else None
        data["roles"] = [r.value for r in self.roles]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "GameResult":
        data = dict(data)
        data["winner"] = TeamDTO(data["winner"]) if data["winner"] else None
        data["roles"] = [IdentityDTO(r) for r in data["roles"]]
        data["deaths"] = [tuple(d) for d in data["deaths"]]
        return cls(**data)


def bot_specs(players: int) -> list[PlayerSpec]:
    return [
        PlayerSpec(user_id=i + 1, user_name=f"Bot{i}", is_bot=True, character="Sim", life=LIFE)
        for i in range(players)
    ]


def agent_seed(game_seed: int, seat: int) -> int:
    """Semente propria de cada agente, derivada da partida: a partida inteira se repete."""
    return game_seed * 100 + seat


def make_agent(spec: str, seed: int) -> Agent:
    """Monta um agente a partir de um texto, para a CLI e para os processos do Pool.

    Formatos: "heuristic", "bayes", "bayes:dificil", "bayes:medio:n=10",
    "bayes:medio:params=results/tune/best.json", "bayes:medio:value=app/models/value_net_v1.pt",
    "bayes:medio:beta=2:eps=0.1".
    """
    # ":" separa as opcoes, menos quando vem antes de uma barra (C:/... no Windows)
    kind, *parts = re.split(r":(?![\\/])", spec)
    if kind == "heuristic":
        from app.bot.heuristic_agent import HeuristicAgent

        return HeuristicAgent(seed, name=spec)
    if kind != "bayes":
        raise ValueError(f"Agente desconhecido: {spec}")

    from app.bot.agent import BayesAgent
    from app.bot.likelihood import SoftmaxLikelihood
    from app.dtos.game_state import DifficultyDTO

    difficulty = DifficultyDTO.MEDIO
    options: dict[str, str] = {}
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            options[key] = value
        else:
            difficulty = DifficultyDTO(part)

    kwargs: dict = {"seed": seed, "difficulty": difficulty, "name": spec}
    if "n" in options:
        kwargs["n_samples"] = int(options["n"])
    if "beta" in options or "eps" in options:
        kwargs["model"] = SoftmaxLikelihood(
            beta=float(options.get("beta", 1.0)), epsilon=float(options.get("eps", 0.05))
        )
    if "params" in options:
        kwargs["params"] = _load_params(options["params"])
    if "value" in options:
        from app.bot.value_eval import value_evaluator_factory

        kwargs["evaluator_factory"] = value_evaluator_factory(options["value"])
    return BayesAgent(**kwargs)


@lru_cache(maxsize=None)
def _load_params(path: str):
    import json

    from app.bot.evaluation import EvalParams

    with open(path, encoding="utf-8") as f:
        return EvalParams.from_flat(json.load(f))


def build_agents(specs: list[str], seed: int) -> list[Agent]:
    return [make_agent(spec, agent_seed(seed, seat)) for seat, spec in enumerate(specs)]


def play_game(
    seed: int,
    players: int,
    agents: list[Agent],
    max_turns: int = MAX_TURNS,
    belief_model: LikelihoodModel | None = None,
    on_turn: OnTurn | None = None,
) -> GameResult:
    """Uma partida bot contra bot, so com o motor: sem API, banco nem I/O.

    - `belief_model`: se dado, mede a crenca no inicio de cada turno (log-loss do papel real);
    - `on_turn`: chamado com o estado no inicio de cada turno (usado para gravar dados).
    """
    rng = random.Random(seed)
    engine = GameEngine()
    state = engine.new_game(f"sim-{seed}", bot_specs(players), rng, shuffle_roles=True)
    runners = [BotTurnRunner(engine, agent) for agent in agents]
    loss, count = 0.0, 0

    for _ in range(max_turns):
        if state.status is GameStatus.DONE:
            break
        if belief_model is not None:
            turn_loss, turn_count = belief_logloss(state, state.turn.seat, belief_model)
            loss, count = loss + turn_loss, count + turn_count
        if on_turn is not None:
            on_turn(state)
        state = runners[state.turn.seat].play_turn(state)

    roles = [p.identity for p in state.players]
    shots, friendly = shot_counts(state.events, roles)
    return GameResult(
        seed=seed,
        players=players,
        winner=state.winner,
        turns=state.turn_number,
        rounds=state.round_number,
        roles=roles,
        agent_names=[agent.name for agent in agents],
        deaths=causes_of_death(state.events),
        timed_out=state.status is not GameStatus.DONE,
        shots=shots,
        friendly_shots=friendly,
        belief_loss=loss,
        belief_count=count,
    )


def causes_of_death(events: list[GameEvent]) -> list[tuple[int, str]]:
    """O dano sai logo depois do evento que o causa: a causa e o ultimo desses eventos."""
    cause = None
    deaths = []
    for event in events:
        if event.type in CAUSES:
            cause = CAUSES[event.type]
        elif event.type is EventType.DEATH:
            deaths.append((event.target_seat, cause))
    return deaths


def is_ally(a: IdentityDTO, b: IdentityDTO) -> bool:
    """Do mesmo time de verdade. Dois Renegados (8 jogadores) nao sao aliados: so um vence."""
    return team_for(a) is team_for(b) and team_for(a) is not TeamDTO.RENEGADO


def shot_counts(events: list[GameEvent], roles: list[IdentityDTO]) -> tuple[list[int], list[int]]:
    shots = [0] * len(roles)
    friendly = [0] * len(roles)
    for event in events:
        if event.type is EventType.SHOT and event.actor_seat is not None:
            shots[event.actor_seat] += 1
            if is_ally(roles[event.actor_seat], roles[event.target_seat]):
                friendly[event.actor_seat] += 1
    return shots, friendly


def belief_logloss(state: EngineState, seat: int, model: LikelihoodModel) -> tuple[float, int]:
    """Soma de -log P(papel real) sobre os jogadores que `seat` nao conhece, e quantos sao.

    Usa so a observacao do jogador para montar a crenca; o estado real so da o gabarito.
    """
    obs = build_observation(state, seat)
    belief = infer(obs, model)
    total, count = 0.0, 0
    for p in obs.players:
        if p.seat == seat or p.public_identity is not None:
            continue
        prob = belief.marginal(p.seat).get(state.players[p.seat].identity, 0.0)
        total -= math.log(max(prob, 1e-12))
        count += 1
    return total, count
