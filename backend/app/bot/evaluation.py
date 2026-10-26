import math

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
_RENEGADE_ENDGAME = {**_RENEGADE, XERIFE: -1.5}

DEATH_SCORE = -0.5  # morto vale menos que vida zero: ele para de agir
ARROW_RISK = 0.3
HEURISTIC_SCALE = 0.9  # deixa vitoria e derrota (+1/-1) sempre acima de qualquer heuristica


def health(life: int, max_life: int) -> float:
    """Concava: a ultima vida vale mais que a primeira. Quem esta quase morto corre mais
    perigo, entao curar ou finalizar alguem com pouca vida pesa mais."""
    return math.sqrt(life / max_life)


def relation(my_role: IdentityDTO, role: IdentityDTO, renegade_endgame: bool) -> float:
    if my_role in (XERIFE, ASSISTENTE):
        return _SHERIFF_TEAM[role]
    if my_role is FORA_DA_LEI:
        return _OUTLAW[role]
    return (_RENEGADE_ENDGAME if renegade_endgame else _RENEGADE)[role]


def is_renegade_endgame(alive: frozenset[int], world: World, me: int) -> bool:
    return world[me] is RENEGADO and alive == {me, _sheriff(world)}


def evaluate(state: EngineState, world: World, me: int) -> float:
    """V(estado, mundo, eu) em [-1, 1]. A vitoria e decidida pelos papeis do mundo, nao do estado."""
    alive = _alive(state)
    terminal = _terminal_value(alive, world, me)
    if terminal is not None:
        return terminal
    rels = _relations(alive, world, me)
    return _heuristic(state, me, rels, weight=1.0)


class Evaluator:
    """V esperado sob a crenca: E[V] = soma dos mundos de P(mundo) * V(estado, mundo).

    V e linear em rel, entao a soma sobre mundos vira um rel esperado por jogador.
    So depende do conjunto de vivos, que muda pouco: guardamos em cache.
    """

    def __init__(self, belief: Belief, me: int):
        self.me = me
        self.worlds = belief.worlds
        self.probs = belief.probabilities()
        self._cache: dict[frozenset[int], tuple[float, float, list[float]]] = {}

    def value(self, state: EngineState) -> float:
        alive = _alive(state)
        if alive not in self._cache:
            self._cache[alive] = self._summarize(alive, len(state.players))
        terminal, p_ongoing, expected_rels = self._cache[alive]
        if p_ongoing == 0:
            return terminal
        return terminal + _heuristic(state, self.me, expected_rels, weight=p_ongoing)

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
            for seat, rel in enumerate(_relations(alive, world, self.me)):
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


def _relations(alive: frozenset[int], world: World, me: int) -> list[float]:
    endgame = is_renegade_endgame(alive, world, me)
    return [
        1.0 if seat == me else relation(world[me], world[seat], endgame)
        for seat in range(len(world))
    ]


def _heuristic(state: EngineState, me: int, rels: list[float], weight: float) -> float:
    """Soma de rel * saude, menos o risco das flechas que eu seguro. `weight` e P(nao terminou)."""
    raw = 0.0
    for p in state.players:
        score = health(p.life, p.max_life) if p.is_alive else DEATH_SCORE
        raw += rels[p.seat] * score
    mine = state.players[me]
    if mine.is_alive:
        raw -= weight * ARROW_RISK * min(1.0, mine.arrows / mine.max_life)
    return utility_scale(len(state.players)) * raw


def utility_scale(players_total: int) -> float:
    """Quanto vale, em V, uma unidade de rel * saude. Divide pelo maior |raw| possivel para
    ficar em [-1, 1]."""
    norm = 1.0 + ARROW_RISK + 1.5 * (players_total - 1)
    return HEURISTIC_SCALE / norm
