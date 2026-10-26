from collections import Counter
from collections.abc import Callable
from math import comb

from app.engine.dice import DiceFace
from app.engine.rules import RESOLUTION_ORDER, Assignment, GameEngine
from app.engine.seating import valid_targets
from app.engine.state import EngineState, GameStatus, TurnPhase

ValueFn = Callable[[EngineState], float]
Plan = list[Assignment]
# Recebe (alvo, valor) de cada opcao e devolve o alvo escolhido
Chooser = Callable[[list[tuple[int, float]]], int]

MAX_EXHAUSTIVE_PLANS = 500


def next_die(engine: GameEngine, state: EngineState) -> int:
    """O motor exige a ordem 1, 2 e Cerveja; dentro da mesma face, o menor indice."""
    pending = engine.pending_dice(state)
    return min(pending, key=lambda i: (RESOLUTION_ORDER[state.turn.dice[i].face], i))


def candidate_targets(state: EngineState, seat: int, face: DiceFace) -> list[int]:
    """Alvos que vale a pena testar.

    Cerveja em quem esta com a vida cheia nao faz nada: para V essas opcoes sao todas
    iguais, entao basta uma (de preferencia em si mesmo).
    """
    targets = valid_targets(state, seat, face)
    if face is not DiceFace.BEER:
        return targets
    hurt = [t for t in targets if state.players[t].life < state.players[t].max_life]
    full = [t for t in targets if t not in hurt]
    if full:
        hurt.append(seat if seat in full else full[0])
    return sorted(hurt)


def plan_count(engine: GameEngine, state: EngineState, seat: int) -> int:
    """Quantos planos a busca exaustiva visita, sem contar mortes no meio (que so reduzem).

    Dados de mesma face sao intercambiaveis: k dados com n alvos dao C(n+k-1, k) planos.
    """
    faces = Counter(state.turn.dice[i].face for i in engine.pending_dice(state))
    total = 1
    for face, k in faces.items():
        n = max(1, len(candidate_targets(state, seat, face)))
        total *= comb(n + k - 1, k)
    return total


def resolution_options(
    engine: GameEngine,
    state: EngineState,
    seat: int,
    value_fn: ValueFn,
    chooser: Chooser | None = None,
) -> list[tuple[Plan, float]]:
    """Planos candidatos com seus valores: todos se couber, senao um so, montado de forma gulosa."""
    if plan_count(engine, state, seat) <= MAX_EXHAUSTIVE_PLANS:
        return exhaustive_plans(engine, state, seat, value_fn)
    return [greedy_plan(engine, state, seat, value_fn, chooser)]


def exhaustive_plans(
    engine: GameEngine, state: EngineState, seat: int, value_fn: ValueFn
) -> list[tuple[Plan, float]]:
    """Testa todas as combinacoes de alvos. Pega, por exemplo, dois tiros que matam juntos."""
    leaves: list[tuple[Plan, float]] = []

    def visit(current: EngineState, prefix: Plan, previous: EngineState) -> None:
        if not _resolving(current, seat) or not engine.pending_dice(current):
            leaves.append((prefix, value_fn(_finish(engine, current, seat))))
            return
        index = next_die(engine, current)
        face = current.turn.dice[index].face
        targets = candidate_targets(current, seat, face)
        # "Cerveja A em X e B em Y" = "A em Y e B em X": entre dados de mesma face, so alvos
        # em ordem crescente. So vale se ninguem morreu, porque a morte muda os alvos validos.
        if prefix and _same_face(previous, prefix[-1], face) and _same_alive(previous, current):
            targets = [t for t in targets if t >= prefix[-1].target_seat]
        for target in targets:
            assignment = Assignment(dice_index=index, target_seat=target)
            visit(engine.resolve_one(current, seat, assignment), prefix + [assignment], current)

    visit(state, [], state)
    return [(_complete(engine, state, seat, plan), value) for plan, value in leaves]


def greedy_plan(
    engine: GameEngine,
    state: EngineState,
    seat: int,
    value_fn: ValueFn,
    chooser: Chooser | None = None,
) -> tuple[Plan, float]:
    """Um dado por vez, na ordem 1, 2 e Cerveja, escolhendo o alvo dado o que ja foi decidido."""
    chooser = chooser or _argmax
    plan: Plan = []
    current = state
    while _resolving(current, seat) and engine.pending_dice(current):
        index = next_die(engine, current)
        children = {
            target: engine.resolve_one(current, seat, Assignment(index, target))
            for target in candidate_targets(current, seat, current.turn.dice[index].face)
        }
        target = chooser([(t, value_fn(child)) for t, child in children.items()])
        plan.append(Assignment(dice_index=index, target_seat=target))
        current = children[target]
    return _complete(engine, state, seat, plan), value_fn(_finish(engine, current, seat))


def _argmax(options: list[tuple[int, float]]) -> int:
    return max(options, key=lambda o: o[1])[0]


def _same_face(state: EngineState, assignment: Assignment, face: DiceFace) -> bool:
    return state.turn.dice[assignment.dice_index].face is face


def _same_alive(before: EngineState, after: EngineState) -> bool:
    return len(before.alive_players()) == len(after.alive_players())


def _resolving(state: EngineState, seat: int) -> bool:
    return (
        state.status is GameStatus.RUNNING
        and state.turn.seat == seat
        and state.turn.phase is TurnPhase.RESOLVING
    )


def _finish(engine: GameEngine, state: EngineState, seat: int) -> EngineState:
    """Sem dados com alvo, ainda falta a Gatling e passar a vez: o motor faz isso no resolve vazio."""
    if _resolving(state, seat) and not engine.pending_dice(state):
        return engine.resolve(state, seat, [])
    return state


def _complete(engine: GameEngine, root: EngineState, seat: int, plan: Plan) -> Plan:
    """Se a partida acabou no meio, o motor ainda exige alvo para todo dado pendente.

    Esses dados nao chegam a ser aplicados; qualquer alvo valido no inicio serve.
    """
    chosen = {a.dice_index for a in plan}
    filler = [
        Assignment(index, valid_targets(root, seat, root.turn.dice[index].face)[0])
        for index in engine.pending_dice(root)
        if index not in chosen
    ]
    return plan + filler
