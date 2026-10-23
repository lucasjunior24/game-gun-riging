# Fase 1: motor de regras no backend

Este documento detalha como implementar a Fase 1 do `PLANO_IMPLEMENTACAO_IA.md`: um motor de regras de Bang! The Dice Game em Python puro, que vira a única fonte de verdade do jogo para o humano, para os bots e, mais tarde, para o simulador da IA.

## Objetivo da fase

- Toda regra do jogo fica em `backend/app/engine/`, sem FastAPI, sem banco e sem Pydantic.
- O `GameService` vira um **adaptador**: guarda o estado do motor e traduz para os DTOs que a API já devolve.
- A **API atual continua funcionando** com o front como está. A troca de endpoints fica para a Fase 2.
- Bugs corrigidos já nesta fase:
  - o bot passa a rolar dados de verdade, em vez de usar a própria vida como número de tiros;
  - a vitória do Renegado passa a existir;
  - o índice do jogador da vez deixa de pular jogadores quando alguém morre;
  - o servidor deixa de aceitar faces de dados vindas do cliente e passa a controlar as 3 rolagens;
  - tiros só são aceitos em alvos que estão na distância certa.

Fora do escopo desta fase: poderes dos personagens (ficam com um ponto de extensão), crença bayesiana e Monte Carlo (Fase 4), novos endpoints (Fase 2).

## Conceitos usados

### Servidor autoritativo
O cliente só pede ações ("rolar estes dados", "atirar com este dado neste jogador"). O servidor decide os resultados e valida tudo. Hoje o front manda a face dos dados travados e controla o limite de rolagens. Com o motor, ele manda só **índices**, e o servidor rejeita o que for contra a regra.

### Núcleo puro e casca fina
O motor é um conjunto de funções sobre um estado em memória. Ele não sabe o que é HTTP, banco ou DTO. A camada de serviço faz a tradução. Isso permite:
- testar regras sem subir a API;
- rodar milhares de partidas por segundo no simulador da Fase 5;
- reaproveitar o mesmo código para o humano e para os bots.

### Máquina de estados do turno
O turno passa por fases explícitas, e cada ação só é aceita na fase certa:

```text
ROLANDO ──(3 rolagens, parar ou 3 dinamites)──▶ RESOLVENDO ──(dados resolvidos)──▶ próximo turno
```

Fora de fase, o motor levanta `RuleViolation`. Isso elimina vários estados impossíveis de uma vez, como rolar depois de atirar ou atirar duas vezes.

### Registro de eventos
Toda mudança gera um evento tipado (`DADO_ROLADO`, `FLECHA`, `ATAQUE_INDIGENA`, `TIRO`, `CERVEJA`, `GATLING`, `DINAMITE`, `MORTE`, `VITORIA`). O registro tem três usos:
- o front anima a jogada evento por evento (Fase 3);
- a IA atualiza a crença a partir do que aconteceu (Fase 4);
- os testes conferem exatamente o que aconteceu.

### Aleatoriedade injetável
O motor nunca chama `random` global. Cada partida recebe um `random.Random`. Com uma semente fixa, a partida é **reproduzível**: um bug vira um teste que falha sempre igual, e o simulador pode comparar duas políticas nas mesmas rolagens.

### Ações atômicas com clone
Uma resolução com vários dados é aplicada numa cópia do estado. Se qualquer dado for inválido, a cópia é descartada e o estado original fica intacto. O mesmo `clone()` serve depois para a simulação de Monte Carlo testar jogadas sem mexer na partida real.

### Informação pública e privada
O estado interno sabe todas as identidades. Os eventos guardam a identidade só quando ela é pública (o Xerife, ou alguém que morreu). Assim, o histórico entregue à IA não vaza papéis ocultos, o que hoje acontece em `GameActionHistoryDTO`.

## Regras implementadas

- **Papéis por número de jogadores (4 a 8):**
  - 4: Xerife, Renegado, 2 Foras da lei.
  - 5: + Assistente. 6: + Fora da lei. 7: + Assistente. 8: + Renegado.
- **Vida:** a do personagem, com +2 para o Xerife. Cerveja nunca passa da vida máxima.
- **Ordem do turno:** o Xerife começa, e os turnos seguem no sentido horário entre os vivos.
- **Rolagem:**
  - Na primeira rolagem saem os 5 dados. Nas outras duas, o jogador escolhe quais rolar de novo.
  - Dinamite fica travada e não pode ser rolada de novo.
  - Cada Flecha que sai é resolvida na hora: o jogador pega uma flecha da pilha de 9.
  - Se a pilha acabar, acontece o ataque indígena: cada vivo perde 1 de vida por flecha, e todas as flechas voltam para a pilha.
  - Com 3 Dinamites ou mais, o jogador perde 1 de vida e as rolagens acabam.
- **Resolução**, na ordem 1 → 2 → Cerveja → Gatling:
  - Todo 1, 2 e Cerveja precisa ser usado.
  - **1:** dano em um jogador a distância 1.
  - **2:** dano em um jogador a distância 2.
  - **Cerveja:** +1 de vida em qualquer jogador vivo, inclusive o próprio.
  - **Gatling (3 ou mais):** 1 de dano em todos os outros jogadores, e quem rolou devolve suas flechas. Acontece uma vez só, mesmo com 4 ou 5 Gatlings.
- **Distância:** contada pelo menor caminho no círculo, ignorando mortos. Com 3 vivos ou menos, o "2" atinge a distância 1.
- **Morte:** com vida 0 o jogador morre, revela o papel e devolve as flechas à pilha. Se quem morre é o jogador da vez, o turno acaba.
- **Vitória**, conferida a cada morte:
  - Xerife morto e só o Renegado vivo: **Renegado** vence.
  - Xerife morto em qualquer outro caso: **Foras da lei** vencem.
  - Xerife vivo e nenhum Fora da lei nem Renegado vivo: **time do Xerife** vence.

## Arquivos

### Novos

| Arquivo | Responsabilidade |
| --- | --- |
| `backend/app/engine/__init__.py` | Exporta `GameEngine`, `EngineState` e tipos principais |
| `backend/app/engine/errors.py` | `RuleViolation` |
| `backend/app/engine/dice.py` | `DiceFace`, `Die`, constantes de dados |
| `backend/app/engine/roles.py` | Distribuição de papéis e times |
| `backend/app/engine/events.py` | `EventType`, `GameEvent` |
| `backend/app/engine/state.py` | `EnginePlayer`, `TurnState`, `EngineState`, `TurnPhase` |
| `backend/app/engine/seating.py` | Distâncias e alvos válidos |
| `backend/app/engine/rules.py` | `GameEngine`: setup, rolagem, resolução, dano, morte, vitória, turnos |
| `backend/app/services/bot_turn_runner.py` | Bot provisório que joga um turno completo pelo motor |
| `backend/tests/engine/test_seating.py` | Distâncias e alvos |
| `backend/tests/engine/test_rolling.py` | Rolagens, dinamite, limite de 3 |
| `backend/tests/engine/test_arrows.py` | Flechas e ataque indígena |
| `backend/tests/engine/test_resolution.py` | Tiros, cerveja, gatling, atomicidade |
| `backend/tests/engine/test_victory.py` | As três condições de vitória |
| `backend/tests/engine/test_full_game.py` | Partida inteira só com bots, com semente fixa |

### Alterados

| Arquivo | Mudança |
| --- | --- |
| `backend/app/services/game_service.py` | Passa a guardar `EngineState` e a traduzir para DTOs. Remove a lógica de tiro, rolagem e vitória própria. `execute_bot_turn` usa o `BotTurnRunner` |
| `backend/app/dtos/game_state.py` | Campos novos e opcionais em `GameStateDTO` (`phase`, `rolls_left`, `arrows_in_pile`) e em `PublicPlayerDTO` (`max_bullet`). Novo campo `shuffle_roles` em `CreateAuthoritativeGameDTO` |
| `backend/app/dtos/history.py` | `ActionTypeDTO` ganha `DINAMITE` e `MORTE` |
| `backend/app/services/policy_service.py` | Novo método `rank_targets` para escolher entre alvos já válidos. A nota de vida passa a usar `vida / vida máxima` |
| `backend/app/views/game_state.py` | `roll_dice` e `finish_turn` passam a converter `RuleViolation` em HTTP 400, como as outras rotas já fazem com `ValueError` |
| `backend/tests/services/*.py` | Ajustes onde os testes contavam com a remoção de mortos da lista ou com tiros sem distância |

O front não precisa mudar nesta fase. As respostas continuam no mesmo formato, só com campos a mais.

## Código

Os trechos abaixo são o esqueleto da implementação. Os nomes e a estrutura são os que eu usaria. Detalhes menores podem mudar durante a escrita e os testes.

### `app/engine/errors.py`

```python
class RuleViolation(ValueError):
    """Ação proibida pelas regras do jogo."""
```

Herdar de `ValueError` faz as rotas que já tratam `ValueError` devolverem 400 sem mudança.

### `app/engine/dice.py`

```python
from dataclasses import dataclass
from enum import Enum


class DiceFace(Enum):
    SHOT_1 = "1"
    SHOT_2 = "2"
    DYNAMITE = "Dinamite"
    BEER = "Cerveja"
    ARROW = "Flecha"
    GATLING = "Metralhadora"


FACES = tuple(DiceFace)
DICE_COUNT = 5
MAX_ROLLS = 3
DYNAMITE_LIMIT = 3
GATLING_MIN = 3


@dataclass
class Die:
    index: int
    face: DiceFace | None = None
    locked: bool = False

    @property
    def can_reroll(self) -> bool:
        return self.face is not DiceFace.DYNAMITE
```

Hoje a face aparece como `"Flexa"` no backend e no front. O adaptador continua mandando `"Flexa"` até a Fase 3, para não quebrar a tela.

### `app/engine/roles.py`

```python
import random

from app.dtos.character import IdentityDTO, TeamDTO

ROLE_DISTRIBUTION: dict[int, list[IdentityDTO]] = {
    4: [IdentityDTO.XERIFE, IdentityDTO.RENEGADO, IdentityDTO.FORA_DA_LEI, IdentityDTO.FORA_DA_LEI],
}
ROLE_DISTRIBUTION[5] = ROLE_DISTRIBUTION[4] + [IdentityDTO.ASSISTENTE]
ROLE_DISTRIBUTION[6] = ROLE_DISTRIBUTION[5] + [IdentityDTO.FORA_DA_LEI]
ROLE_DISTRIBUTION[7] = ROLE_DISTRIBUTION[6] + [IdentityDTO.ASSISTENTE]
ROLE_DISTRIBUTION[8] = ROLE_DISTRIBUTION[7] + [IdentityDTO.RENEGADO]


def deal_roles(players_total: int, rng: random.Random, shuffle: bool = True) -> list[IdentityDTO]:
    if players_total not in ROLE_DISTRIBUTION:
        raise ValueError("Bang! Dice suporta de 4 a 8 jogadores")
    roles = list(ROLE_DISTRIBUTION[players_total])
    if shuffle:
        rng.shuffle(roles)
    return roles


def team_for(identity: IdentityDTO) -> TeamDTO:
    if identity in (IdentityDTO.XERIFE, IdentityDTO.ASSISTENTE):
        return TeamDTO.XERIFE
    if identity is IdentityDTO.FORA_DA_LEI:
        return TeamDTO.FORA_DA_LEI
    return TeamDTO.RENEGADO
```

`shuffle=False` mantém o comportamento atual, em que o humano é sempre o Xerife. Hoje a tela não mostra ao humano o próprio papel quando ele não é o Xerife, então o sorteio só deve ser ligado por padrão na Fase 3.

### `app/engine/events.py`

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.dtos.character import IdentityDTO


class EventType(Enum):
    TURN_STARTED = "TURNO_INICIADO"
    DICE_ROLLED = "DADO_ROLADO"
    ARROW_TAKEN = "FLECHA"
    INDIAN_ATTACK = "ATAQUE_INDIGENA"
    DYNAMITE_EXPLODED = "DINAMITE"
    SHOT = "TIRO"
    BEER = "CERVEJA"
    GATLING = "GATLING"
    DAMAGE = "DANO"
    DEATH = "MORTE"
    VICTORY = "VITORIA"


@dataclass
class GameEvent:
    type: EventType
    round_number: int
    turn_number: int
    actor_seat: int | None = None
    target_seat: int | None = None
    amount: int = 0
    # Preenchidos só quando a identidade é pública (Xerife ou morto)
    actor_public_identity: IdentityDTO | None = None
    target_public_identity: IdentityDTO | None = None
    data: dict[str, Any] = field(default_factory=dict)
```

### `app/engine/state.py`

```python
import copy
import random
from dataclasses import dataclass, field
from enum import Enum

from app.dtos.character import IdentityDTO, TeamDTO
from app.engine.dice import DICE_COUNT, Die
from app.engine.events import GameEvent

ARROWS_TOTAL = 9


class TurnPhase(Enum):
    ROLLING = "ROLANDO"
    RESOLVING = "RESOLVENDO"


class GameStatus(Enum):
    RUNNING = "Running"
    DONE = "Done"


@dataclass
class EnginePlayer:
    seat: int
    user_id: int
    user_name: str
    identity: IdentityDTO
    max_life: int
    life: int
    is_bot: bool
    character: str = ""
    power: str = ""
    arrows: int = 0
    revealed: bool = False

    @property
    def is_alive(self) -> bool:
        return self.life > 0

    @property
    def public_identity(self) -> IdentityDTO | None:
        if self.identity is IdentityDTO.XERIFE or self.revealed:
            return self.identity
        return None


@dataclass
class TurnState:
    seat: int
    dice: list[Die] = field(default_factory=lambda: [Die(index=i) for i in range(DICE_COUNT)])
    rolls_used: int = 0
    phase: TurnPhase = TurnPhase.ROLLING


@dataclass
class EngineState:
    game_id: str
    players: list[EnginePlayer]
    rng: random.Random
    turn: TurnState
    arrows_in_pile: int = ARROWS_TOTAL
    round_number: int = 1
    turn_number: int = 1
    status: GameStatus = GameStatus.RUNNING
    winner: TeamDTO | None = None
    events: list[GameEvent] = field(default_factory=list)

    @property
    def current_player(self) -> EnginePlayer:
        return self.players[self.turn.seat]

    def alive_players(self) -> list[EnginePlayer]:
        return [p for p in self.players if p.is_alive]

    def clone(self) -> "EngineState":
        return copy.deepcopy(self)
```

Jogadores mortos **continuam na lista**. A posição (`seat`) de cada um nunca muda, e isso corrige o bug do índice do jogador da vez.

### `app/engine/seating.py`

```python
from app.engine.dice import DiceFace
from app.engine.state import EngineState


def distance(state: EngineState, from_seat: int, to_seat: int) -> int:
    alive = [p.seat for p in state.players if p.is_alive]
    i, j = alive.index(from_seat), alive.index(to_seat)
    steps = abs(i - j)
    return min(steps, len(alive) - steps)


def valid_targets(state: EngineState, shooter_seat: int, face: DiceFace) -> list[int]:
    alive = state.alive_players()
    if face is DiceFace.BEER:
        return [p.seat for p in alive]

    wanted = 1 if face is DiceFace.SHOT_1 else 2
    if len(alive) <= 3:
        wanted = 1
    return [
        p.seat
        for p in alive
        if p.seat != shooter_seat and distance(state, shooter_seat, p.seat) == wanted
    ]
```

### `app/engine/rules.py`

```python
import random
from dataclasses import dataclass

from app.dtos.character import IdentityDTO, TeamDTO
from app.engine.dice import DYNAMITE_LIMIT, FACES, GATLING_MIN, MAX_ROLLS, DiceFace
from app.engine.errors import RuleViolation
from app.engine.events import EventType, GameEvent
from app.engine.roles import deal_roles
from app.engine.seating import valid_targets
from app.engine.state import (
    ARROWS_TOTAL,
    EnginePlayer,
    EngineState,
    GameStatus,
    TurnPhase,
    TurnState,
)

TARGETED_FACES = (DiceFace.SHOT_1, DiceFace.SHOT_2, DiceFace.BEER)
RESOLUTION_ORDER = {DiceFace.SHOT_1: 0, DiceFace.SHOT_2: 1, DiceFace.BEER: 2}


@dataclass
class PlayerSpec:
    user_id: int
    user_name: str
    is_bot: bool
    character: str
    life: int
    power: str = ""


@dataclass
class Assignment:
    dice_index: int
    target_seat: int


class GameEngine:
    # ---------- setup ----------

    def new_game(
        self,
        game_id: str,
        specs: list[PlayerSpec],
        rng: random.Random,
        shuffle_roles: bool = True,
    ) -> EngineState:
        roles = deal_roles(len(specs), rng, shuffle_roles)
        players = []
        for seat, (spec, identity) in enumerate(zip(specs, roles)):
            bonus = 2 if identity is IdentityDTO.XERIFE else 0
            players.append(
                EnginePlayer(
                    seat=seat,
                    user_id=spec.user_id,
                    user_name=spec.user_name,
                    identity=identity,
                    max_life=spec.life + bonus,
                    life=spec.life + bonus,
                    is_bot=spec.is_bot,
                    character=spec.character,
                    power=spec.power,
                )
            )
        sheriff_seat = next(p.seat for p in players if p.identity is IdentityDTO.XERIFE)
        state = EngineState(
            game_id=game_id, players=players, rng=rng, turn=TurnState(seat=sheriff_seat)
        )
        self._emit(state, EventType.TURN_STARTED, actor_seat=sheriff_seat)
        return state

    # ---------- rolagem ----------

    def roll(self, state: EngineState, seat: int, reroll_indexes: set[int] | None = None) -> None:
        turn = self._require_phase(state, seat, TurnPhase.ROLLING)
        if turn.rolls_used >= MAX_ROLLS:
            raise RuleViolation("Sem rolagens restantes")

        if turn.rolls_used == 0:
            indexes = {die.index for die in turn.dice}
        else:
            indexes = set(reroll_indexes or ())
            if not indexes:
                raise RuleViolation("Escolha ao menos um dado para rolar de novo")
            for index in indexes:
                if not turn.dice[index].can_reroll:
                    raise RuleViolation("Dinamite não pode ser rolada de novo")

        for index in sorted(indexes):
            die = turn.dice[index]
            die.face = state.rng.choice(FACES)
            die.locked = die.face is DiceFace.DYNAMITE
            self._emit(state, EventType.DICE_ROLLED, actor_seat=seat, data={"index": index, "face": die.face.value})
            if die.face is DiceFace.ARROW:
                self._take_arrow(state, seat)
                if self._turn_interrupted(state, seat):
                    return

        turn.rolls_used += 1

        dynamites = sum(1 for die in turn.dice if die.face is DiceFace.DYNAMITE)
        if dynamites >= DYNAMITE_LIMIT:
            self._emit(state, EventType.DYNAMITE_EXPLODED, actor_seat=seat)
            self._damage(state, seat, seat, 1)
            if self._turn_interrupted(state, seat):
                return
            turn.phase = TurnPhase.RESOLVING
        elif turn.rolls_used == MAX_ROLLS:
            turn.phase = TurnPhase.RESOLVING

    def stop_rolling(self, state: EngineState, seat: int) -> None:
        turn = self._require_phase(state, seat, TurnPhase.ROLLING)
        if turn.rolls_used == 0:
            raise RuleViolation("Role os dados ao menos uma vez")
        turn.phase = TurnPhase.RESOLVING

    # ---------- resolução ----------

    def pending_dice(self, state: EngineState) -> list[int]:
        return [die.index for die in state.turn.dice if die.face in TARGETED_FACES]

    def resolve(self, state: EngineState, seat: int, assignments: list[Assignment]) -> EngineState:
        """Aplica a resolução numa cópia e devolve o novo estado. Se algo for inválido, nada muda."""
        self._require_phase(state, seat, TurnPhase.RESOLVING)
        draft = state.clone()

        by_index = {a.dice_index: a for a in assignments}
        if sorted(by_index) != sorted(self.pending_dice(draft)) or len(by_index) != len(assignments):
            raise RuleViolation("Cada dado de 1, 2 e Cerveja precisa de exatamente um alvo")

        ordered = sorted(assignments, key=lambda a: (RESOLUTION_ORDER[draft.turn.dice[a.dice_index].face], a.dice_index))
        for assignment in ordered:
            face = draft.turn.dice[assignment.dice_index].face
            # A validação acontece no estado do momento: mortes anteriores mudam as distâncias
            if assignment.target_seat not in valid_targets(draft, seat, face):
                raise RuleViolation(f"Alvo inválido para o dado {assignment.dice_index}")
            if face is DiceFace.BEER:
                self._heal(draft, seat, assignment.target_seat)
            else:
                self._emit(draft, EventType.SHOT, actor_seat=seat, target_seat=assignment.target_seat, amount=1)
                self._damage(draft, seat, assignment.target_seat, 1)
            if draft.status is GameStatus.DONE or not draft.players[seat].is_alive:
                return draft

        gatlings = sum(1 for die in draft.turn.dice if die.face is DiceFace.GATLING)
        if gatlings >= GATLING_MIN:
            self._gatling(draft, seat)
            if draft.status is GameStatus.DONE:
                return draft

        self._next_turn(draft)
        return draft

    # ---------- efeitos ----------

    def _take_arrow(self, state: EngineState, seat: int) -> None:
        state.players[seat].arrows += 1
        state.arrows_in_pile -= 1
        self._emit(state, EventType.ARROW_TAKEN, actor_seat=seat)
        if state.arrows_in_pile == 0:
            self._indian_attack(state)

    def _indian_attack(self, state: EngineState) -> None:
        self._emit(state, EventType.INDIAN_ATTACK)
        for player in state.alive_players():
            if player.arrows:
                self._damage(state, None, player.seat, player.arrows)
        for player in state.players:
            player.arrows = 0
        state.arrows_in_pile = ARROWS_TOTAL

    def _gatling(self, state: EngineState, seat: int) -> None:
        self._emit(state, EventType.GATLING, actor_seat=seat)
        shooter = state.players[seat]
        state.arrows_in_pile += shooter.arrows
        shooter.arrows = 0
        for player in state.alive_players():
            if player.seat != seat:
                self._damage(state, seat, player.seat, 1)

    def _heal(self, state: EngineState, seat: int, target_seat: int) -> None:
        target = state.players[target_seat]
        healed = min(1, target.max_life - target.life)
        target.life += healed
        self._emit(state, EventType.BEER, actor_seat=seat, target_seat=target_seat, amount=healed)

    def _damage(self, state: EngineState, source_seat: int | None, target_seat: int, amount: int) -> None:
        target = state.players[target_seat]
        if not target.is_alive:
            return
        target.life = max(0, target.life - amount)
        self._emit(state, EventType.DAMAGE, actor_seat=source_seat, target_seat=target_seat, amount=amount)
        if not target.is_alive:
            self._kill(state, target)

    def _kill(self, state: EngineState, player: EnginePlayer) -> None:
        player.revealed = True
        state.arrows_in_pile += player.arrows
        player.arrows = 0
        self._emit(state, EventType.DEATH, target_seat=player.seat)
        self._check_winner(state)

    # ---------- vitória e turnos ----------

    def _check_winner(self, state: EngineState) -> None:
        if state.status is GameStatus.DONE:
            return
        alive = state.alive_players()
        sheriff_alive = any(p.identity is IdentityDTO.XERIFE for p in alive)
        enemies_alive = any(p.identity in (IdentityDTO.FORA_DA_LEI, IdentityDTO.RENEGADO) for p in alive)

        if not sheriff_alive:
            only_renegade = len(alive) == 1 and alive[0].identity is IdentityDTO.RENEGADO
            state.winner = TeamDTO.RENEGADO if only_renegade else TeamDTO.FORA_DA_LEI
        elif not enemies_alive:
            state.winner = TeamDTO.XERIFE
        else:
            return
        state.status = GameStatus.DONE
        self._emit(state, EventType.VICTORY, data={"winner": state.winner.value})

    def _turn_interrupted(self, state: EngineState, seat: int) -> bool:
        if state.status is GameStatus.DONE:
            return True
        if not state.players[seat].is_alive:
            self._next_turn(state)
            return True
        return False

    def _next_turn(self, state: EngineState) -> None:
        current = state.turn.seat
        total = len(state.players)
        for step in range(1, total + 1):
            seat = (current + step) % total
            if state.players[seat].is_alive:
                break
        if seat <= current:
            state.round_number += 1
        state.turn_number += 1
        state.turn = TurnState(seat=seat)
        self._emit(state, EventType.TURN_STARTED, actor_seat=seat)

    # ---------- utilidades ----------

    def _require_phase(self, state: EngineState, seat: int, phase: TurnPhase) -> TurnState:
        if state.status is GameStatus.DONE:
            raise RuleViolation("A partida já terminou")
        if state.turn.seat != seat:
            raise RuleViolation("Não é a vez deste jogador")
        if state.turn.phase is not phase:
            raise RuleViolation(f"Ação não permitida na fase {state.turn.phase.value}")
        return state.turn

    def _emit(self, state: EngineState, event_type: EventType, actor_seat=None, target_seat=None, amount=0, data=None) -> None:
        actor = state.players[actor_seat] if actor_seat is not None else None
        target = state.players[target_seat] if target_seat is not None else None
        state.events.append(
            GameEvent(
                type=event_type,
                round_number=state.round_number,
                turn_number=state.turn_number,
                actor_seat=actor_seat,
                target_seat=target_seat,
                amount=amount,
                actor_public_identity=actor.public_identity if actor else None,
                target_public_identity=target.public_identity if target else None,
                data=data or {},
            )
        )
```

Dois pontos de atenção:
- `resolve` devolve um **novo** estado. O serviço substitui o estado guardado pelo retorno. Se for levantada `RuleViolation`, o estado guardado continua o mesmo.
- O `rng` é copiado junto no `clone()`. Para o Monte Carlo isso é desejado: cada simulação continua a sequência de forma independente da partida real.

### `app/services/bot_turn_runner.py` (bot provisório)

Um bot simples que joga **pelas regras**, até a IA da Fase 4 substituí-lo. Ele reaproveita o `ShotPolicyService` só para escolher entre alvos que o motor já diz serem válidos.

```python
from app.dtos.character import IdentityDTO
from app.engine import GameEngine
from app.engine.dice import MAX_ROLLS, DiceFace
from app.engine.rules import Assignment
from app.engine.seating import valid_targets
from app.engine.state import EngineState, GameStatus, TurnPhase
from app.services.policy_service import ShotPolicyService


class BotTurnRunner:
    def __init__(self, engine: GameEngine, policy: ShotPolicyService):
        self.engine = engine
        self.policy = policy

    def play_turn(self, state: EngineState) -> EngineState:
        seat = state.turn.seat
        self.engine.roll(state, seat)
        while self._still_rolling(state, seat) and state.turn.rolls_used < MAX_ROLLS:
            reroll = self._choose_rerolls(state, seat)
            if not reroll:
                self.engine.stop_rolling(state, seat)
                break
            self.engine.roll(state, seat, reroll)

        if not self._still_resolving(state, seat):
            return state
        return self.engine.resolve(state, seat, self._choose_assignments(state, seat))

    def _choose_rerolls(self, state: EngineState, seat: int) -> set[int]:
        me = state.players[seat]
        reroll = set()
        for die in state.turn.dice:
            if not die.can_reroll:
                continue
            if die.face is DiceFace.ARROW:
                reroll.add(die.index)
            elif die.face is DiceFace.BEER and me.life == me.max_life:
                reroll.add(die.index)
        return reroll

    def _choose_assignments(self, state: EngineState, seat: int) -> list[Assignment]:
        assignments = []
        for index in self.engine.pending_dice(state):
            face = state.turn.dice[index].face
            candidates = valid_targets(state, seat, face)
            if face is DiceFace.BEER:
                target = self._choose_beer_target(state, seat, candidates)
            else:
                target = self.policy.rank_targets(state, seat, candidates)[0]
            assignments.append(Assignment(dice_index=index, target_seat=target))
        return assignments

    def _choose_beer_target(self, state: EngineState, seat: int, candidates: list[int]) -> int:
        me = state.players[seat]
        if me.identity in (IdentityDTO.ASSISTENTE, IdentityDTO.RENEGADO):
            sheriff = next(p for p in state.players if p.identity is IdentityDTO.XERIFE)
            if sheriff.seat in candidates and sheriff.life < sheriff.max_life and me.life > 2:
                return sheriff.seat
        return seat

    def _still_rolling(self, state, seat) -> bool:
        return state.status is GameStatus.RUNNING and state.turn.seat == seat and state.turn.phase is TurnPhase.ROLLING

    def _still_resolving(self, state, seat) -> bool:
        return state.status is GameStatus.RUNNING and state.turn.seat == seat and state.turn.phase is TurnPhase.RESOLVING
```

A escolha de cerveja usa a identidade do **próprio** bot, que ele conhece, e a do Xerife, que é pública. Ela não espia papéis ocultos.

Uma ressalva sobre o `resolve` dentro do bot: os alvos são escolhidos todos antes de aplicar. Se um tiro anterior matar alguém e mudar as distâncias, um alvo pode ficar inválido. Para o bot provisório, a saída é resolver dado a dado: chamar `resolve_one` (variante de `resolve` com um único dado) em sequência, escolhendo o próximo alvo depois de cada aplicação. Eu implementaria `resolve` em cima de `resolve_one` justamente para isso.

### `app/services/policy_service.py` (mudanças)

```python
def rank_targets(self, state: EngineState, seat: int, candidates: list[int]) -> list[int]:
    """Ordena alvos já validados pelo motor, do melhor para o pior."""
    execution = self._execution_from_engine(state, seat, candidates)
    scored = [
        (self._score_candidate_by_belief(execution, execution.one_distance, "1", candidate), candidate)
        for candidate in execution.one_distance.players_options
    ]
    by_name = {state.players[s].user_name: s for s in candidates}
    return [by_name[p.user_name] for _, p in sorted(scored, key=lambda item: item[0], reverse=True)]
```

E a nota de vida passa a usar a escala real:

```python
# antes: life_score = max(0.0, min(1.0, (3.0 - float(candidate.bullet)) / 3.0))
life_score = 1.0 - candidate.bullet / max(1, candidate.max_bullet)
```

`_execution_from_engine` monta o `ExecuteDicesDTO` atual a partir do estado do motor e do histórico só com identidades públicas. Ele é uma ponte provisória até a Fase 4, quando a política passa a ler o estado do motor diretamente.

### `app/services/game_service.py` (adaptador)

```python
class GameService:
    _games: dict[str, EngineState] = {}

    def __init__(self):
        self.engine = GameEngine()
        self.belief_service = BeliefService()

    def create_game(self, command: CreateAuthoritativeGameDTO) -> GameStateDTO:
        specs = self._player_specs(command.player_name, command.players_total)
        state = self.engine.new_game(str(uuid4()), specs, random.Random(), command.shuffle_roles)
        self._games[state.game_id] = state
        return self.to_public_state(state)

    def roll_dice(self, game_id: str, command: RollDiceCommandDTO) -> GameStateDTO:
        state = self._get_game(game_id)
        # O front manda os dados com "locked"; só o índice é usado. A face enviada é ignorada.
        locked = {d.index - 1 for d in command.locked_dice_indexes if d.locked}
        reroll = {die.index for die in state.turn.dice if die.index not in locked and die.can_reroll}
        self.engine.roll(state, state.turn.seat, reroll)
        return self.to_public_state(state)

    def execute_shots(self, game_id: str, command: ExecuteShotsCommandDTO) -> GameStateDTO:
        state = self._get_game(game_id)
        actor = self._seat_by_user_id(state, command.actor_user_id)
        if state.turn.phase is TurnPhase.ROLLING:
            self.engine.stop_rolling(state, actor)
        assignments = self._assignments_from_command(state, actor, command)
        self._games[game_id] = self.engine.resolve(state, actor, assignments)
        return self.to_public_state(self._games[game_id])

    def execute_bot_turn(self, game_id: str) -> GameStateDTO:
        state = self._get_game(game_id)
        if not state.current_player.is_bot:
            raise ValueError(f"Jogador {state.current_player.user_name} nao e um bot")
        runner = BotTurnRunner(self.engine, ShotPolicyService())
        self._games[game_id] = runner.play_turn(state)
        return self.to_public_state(self._games[game_id])
```

Pontos do adaptador:
- `_assignments_from_command` converte "N tiros no jogador X na distância D" do formato atual em um `Assignment` por dado de face `1` ou `2`. Cervejas que o formato atual não sabe expressar vão para o próprio jogador. Na Fase 2 o comando passa a ser por dado.
- `finish_turn` no meio das rolagens: para manter o botão "Passar Turno" funcionando, o adaptador para de rolar e resolve com o mesmo critério do bot. Se o jogador ainda não rolou, rola uma vez antes. Na Fase 2 esse botão some, porque no jogo não existe passar sem resolver os dados.
- `to_public_state` devolve todos os jogadores, inclusive mortos com `is_alive=False`. `revealed_identity` vem de `public_identity`. Os dados são traduzidos para `DiceShowDTO` com `index` começando em 1, como o front espera hoje.
- Os eventos do motor são convertidos para `GameActionHistoryDTO` (`TIRO`, `GATLING`, `CERVEJA`, `INDIOS`, `DINAMITE`, `MORTE`) usando só identidades públicas. Isso mantém o `BeliefService` funcionando e para de vazar papéis ocultos.

## Testes

Para controlar os dados nos testes, um `random.Random` falso que devolve faces pré-definidas:

```python
class ScriptedRng(random.Random):
    def __init__(self, faces: list[DiceFace]):
        super().__init__(0)
        self._faces = list(faces)

    def choice(self, seq):
        if seq is FACES:
            return self._faces.pop(0)
        return super().choice(seq)
```

Exemplos:

```python
def test_tres_dinamites_tiram_uma_vida_e_encerram_rolagem():
    rng = ScriptedRng([DYNAMITE, DYNAMITE, DYNAMITE, SHOT_1, BEER])
    state = engine.new_game("g", specs(5), rng, shuffle_roles=False)
    sheriff = state.current_player
    engine.roll(state, sheriff.seat)
    assert sheriff.life == sheriff.max_life - 1
    assert state.turn.phase is TurnPhase.RESOLVING


def test_renegado_vence_quando_e_o_ultimo_vivo():
    state = game_with_only_sheriff_and_renegade_alive()
    renegade_seat = seat_of(state, IdentityDTO.RENEGADO)
    kill_sheriff_on_renegade_turn(state, renegade_seat)
    assert state.winner is TeamDTO.RENEGADO


def test_tiro_fora_de_alcance_e_rejeitado_sem_alterar_estado():
    state = game_in_resolving_phase(faces=[SHOT_1, ARROW, ARROW, BEER, GATLING])
    before = state.clone()
    with pytest.raises(RuleViolation):
        engine.resolve(state, state.turn.seat, [Assignment(0, seat_at_distance(state, 2)), Assignment(3, state.turn.seat)])
    assert state.players == before.players


def test_morte_nao_pula_o_proximo_jogador():
    state = game_where_seat_0_kills_seat_1()
    state = engine.resolve(state, 0, assignments_that_kill_seat_1(state))
    assert state.turn.seat == 2


def test_partida_completa_entre_bots_termina_com_vencedor():
    for seed in range(50):
        state = engine.new_game("g", specs(5, all_bots=True), random.Random(seed))
        runner = BotTurnRunner(engine, ShotPolicyService())
        for _ in range(500):
            if state.status is GameStatus.DONE:
                break
            state = runner.play_turn(state)
        assert state.status is GameStatus.DONE
        assert state.winner is not None
```

O último teste é o mais valioso: ele roda partidas inteiras com várias sementes e pega qualquer estado travado ou regra que deixe a partida sem fim.

## Ordem de implementação

1. `errors.py`, `dice.py`, `roles.py`, `events.py`, `state.py`, com testes de setup (papéis, vida, Xerife começa).
2. `seating.py`, com testes de distância de 2 a 8 jogadores vivos.
3. `rules.py`, rolagem, flechas e dinamite, com testes.
4. `rules.py`, resolução, gatling, morte e vitória, com testes.
5. `bot_turn_runner.py` e `rank_targets`, com o teste de partida completa.
6. Adaptar `game_service.py` e os DTOs. Ajustar os testes de `tests/services/`.
7. Rodar a API com o front atual e jogar uma partida de ponta a ponta.

## Riscos

- **Formato atual da API:** ele não expressa cerveja nem tiro dado a dado. O adaptador cobre isso com escolhas padrão, que são uma solução provisória até a Fase 2.
- **Testes existentes:** os de `tests/services/` assumem mortos removidos da lista e tiros sem distância. Vários vão precisar de ajuste, e isso é esperado.
- **Poderes dos personagens:** ficam fora. `EnginePlayer.power` já fica guardado para que eles entrem depois como regras extras, sem mudar a estrutura.
