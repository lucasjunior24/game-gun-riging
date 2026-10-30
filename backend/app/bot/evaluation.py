import math
from dataclasses import dataclass, field

from app.bot.belief import Belief
from app.bot.worlds import World
from app.dtos.character import IdentityDTO
from app.engine.roles import team_for
from app.engine.state import EngineState
from app.engine.victory import winner_for

XERIFE = IdentityDTO.XERIFE
ASSISTENTE = IdentityDTO.ASSISTENTE
FORA_DA_LEI = IdentityDTO.FORA_DA_LEI
RENEGADO = IdentityDTO.RENEGADO

# rel(eu, p): quanto a saude de p e boa (+) ou ruim (-) para mim. O Xerife pesa mais
# porque a morte dele decide a partida.
_SHERIFF_TEAM = {XERIFE: 1.5, ASSISTENTE: 1.0, FORA_DA_LEI: -1.0, RENEGADO: -0.7}
_OUTLAW = {XERIFE: -1.5, ASSISTENTE: -1.0, FORA_DA_LEI: 0.7, RENEGADO: -0.3}
# Enquanto ha outros vivos, a morte do Xerife da a vitoria aos Foras da lei:
# o Renegado quer o Xerife vivo. Quando sobram so os dois, ele vira o alvo.
_RENEGADE = {XERIFE: 0.8, ASSISTENTE: -0.5, FORA_DA_LEI: -0.8, RENEGADO: -0.5}

DEATH_SCORE = -0.5  # morto vale menos que vida zero: ele para de agir
ARROW_RISK = 0.3
HEURISTIC_SCALE = 0.9  # deixa vitoria e derrota (+1/-1) sempre acima de qualquer heuristica


@dataclass(frozen=True)
class EvalParams:
    """Os numeros escolhidos a mao da avaliacao. A Fase 5 (app/sim/tune.py) ajusta por busca."""

    sheriff_team: dict[IdentityDTO, float] = field(default_factory=lambda: dict(_SHERIFF_TEAM))
    outlaw: dict[IdentityDTO, float] = field(default_factory=lambda: dict(_OUTLAW))
    renegade: dict[IdentityDTO, float] = field(default_factory=lambda: dict(_RENEGADE))
    renegade_endgame_sheriff: float = -1.5
    death_score: float = DEATH_SCORE
    arrow_risk: float = ARROW_RISK

    def flat(self) -> dict[str, float]:
        """Parametros como {"outlaw.Xerife": -1.5, ...}, para a busca perturbar um a um."""
        out: dict[str, float] = {}
        for name in _TABLES:
            for role, value in getattr(self, name).items():
                out[f"{name}.{role.value}"] = value
        for name in _SCALARS:
            out[name] = getattr(self, name)
        return out

    @classmethod
    def from_flat(cls, values: dict[str, float]) -> "EvalParams":
        base = cls()
        kwargs: dict = {name: dict(getattr(base, name)) for name in _TABLES}
        for key, value in values.items():
            name, _, role = key.partition(".")
            if name in _TABLES:
                kwargs[name][IdentityDTO(role)] = value
            elif name in _SCALARS:
                kwargs[name] = value
            else:
                raise KeyError(f"Parametro desconhecido: {key}")
        return cls(**kwargs)


_TABLES = ("sheriff_team", "outlaw", "renegade")
_SCALARS = ("renegade_endgame_sheriff", "death_score", "arrow_risk")
DEFAULT_PARAMS = EvalParams()


def health(life: int, max_life: int) -> float:
    """Concava: a ultima vida vale mais que a primeira. Quem esta quase morto corre mais
    perigo, entao curar ou finalizar alguem com pouca vida pesa mais."""
    return math.sqrt(life / max_life)


def relation(
    my_role: IdentityDTO,
    role: IdentityDTO,
    renegade_endgame: bool,
    params: EvalParams = DEFAULT_PARAMS,
) -> float:
    if my_role in (XERIFE, ASSISTENTE):
        return params.sheriff_team[role]
    if my_role is FORA_DA_LEI:
        return params.outlaw[role]
    if renegade_endgame and role is XERIFE:
        return params.renegade_endgame_sheriff
    return params.renegade[role]


def is_renegade_endgame(alive: frozenset[int], world: World, me: int) -> bool:
    return world[me] is RENEGADO and alive == {me, _sheriff(world)}


def evaluate(
    state: EngineState, world: World, me: int, params: EvalParams = DEFAULT_PARAMS
) -> float:
    """V(estado, mundo, eu) em [-1, 1]. A vitoria e decidida pelos papeis do mundo, nao do estado."""
    alive = _alive(state)
    terminal = _terminal_value(alive, world, me)
    if terminal is not None:
        return terminal
    rels = _relations(alive, world, me, params)
    return _heuristic(state, me, rels, weight=1.0, params=params)


class Evaluator:
    """V esperado sob a crenca: E[V] = soma dos mundos de P(mundo) * V(estado, mundo).

    V e linear em rel, entao a soma sobre mundos vira um rel esperado por jogador.
    So depende do conjunto de vivos, que muda pouco: guardamos em cache.
    """

    def __init__(self, belief: Belief, me: int, params: EvalParams = DEFAULT_PARAMS):
        self.me = me
        self.params = params
        self.worlds = belief.worlds
        self.probs = belief.probabilities()
        self._cache: dict[frozenset[int], tuple[float, float, list[float]]] = {}

    def value(self, state: EngineState) -> float:
        terminal, p_ongoing, expected_rels = self.summary(state)
        if p_ongoing == 0:
            return terminal
        return terminal + _heuristic(
            state, self.me, expected_rels, weight=p_ongoing, params=self.params
        )

    def summary(self, state: EngineState) -> tuple[float, float, list[float]]:
        """(soma de P(mundo) * V nos mundos em que a partida acabou, P(nao acabou), rel esperado)."""
        alive = _alive(state)
        if alive not in self._cache:
            self._cache[alive] = self._summarize(alive, len(state.players))
        return self._cache[alive]

    def _summarize(self, alive: frozenset[int], total: int) -> tuple[float, float, list[float]]:
        terminal = 0.0
        p_ongoing = 0.0
        expected = [0.0] * total
        for world, p in zip(self.worlds, self.probs):
            outcome = _terminal_value(alive, world, self.me)
            if outcome is not None:
                terminal += p * outcome
                continue
            p_ongoing += p
            for seat, rel in enumerate(_relations(alive, world, self.me, self.params)):
                expected[seat] += p * rel
        return terminal, p_ongoing, expected


def _alive(state: EngineState) -> frozenset[int]:
    return frozenset(p.seat for p in state.players if p.is_alive)


def _sheriff(world: World) -> int:
    return next(seat for seat, role in world.items() if role is XERIFE)


def _terminal_value(alive: frozenset[int], world: World, me: int) -> float | None:
    winner = winner_for(sorted(alive), world)
    if winner is None:
        return None
    return 1.0 if winner is team_for(world[me]) else -1.0


def _relations(alive: frozenset[int], world: World, me: int, params: EvalParams) -> list[float]:
    endgame = is_renegade_endgame(alive, world, me)
    return [
        1.0 if seat == me else relation(world[me], world[seat], endgame, params)
        for seat in range(len(world))
    ]


def _heuristic(
    state: EngineState, me: int, rels: list[float], weight: float, params: EvalParams
) -> float:
    """Soma de rel * saude, menos o risco das flechas que eu seguro. `weight` e P(nao terminou)."""
    raw = 0.0
    for p in state.players:
        score = health(p.life, p.max_life) if p.is_alive else params.death_score
        raw += rels[p.seat] * score
    mine = state.players[me]
    if mine.is_alive:
        raw -= weight * params.arrow_risk * min(1.0, mine.arrows / mine.max_life)
    return utility_scale(len(state.players), params) * raw


def utility_scale(players_total: int, params: EvalParams = DEFAULT_PARAMS) -> float:
    """Quanto vale, em V, uma unidade de rel * saude. Divide pelo maior |raw| possivel para
    ficar em [-1, 1]."""
    biggest_rel = max(abs(v) for name in _TABLES for v in getattr(params, name).values())
    biggest_rel = max(biggest_rel, abs(params.renegade_endgame_sheriff))
    norm = 1.0 + params.arrow_risk + biggest_rel * (players_total - 1)
    return HEURISTIC_SCALE / norm
