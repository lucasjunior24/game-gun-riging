# Guia de Migração do Frontend para Backend Autoritativo

## Visão Geral

Este documento descreve passo a passo como migrar o frontend (`mobile-gun-firing`) para consumir o estado autoritativo do backend, removendo toda lógica de jogo do lado do cliente.

**Princípio:** O frontend pede "quero fazer esta ação". O backend responde "este é o novo estado público do jogo".

---

## 1. Novos DTOs do Frontend (`mobile-gun-firing/src/dtos/`)

### 1.1 Criar `gameState.ts`

Novo arquivo: `mobile-gun-firing/src/dtos/gameState.ts`

```ts
// Representa o jogador público - apenas o que a UI pode mostrar
export type PublicPlayer = {
    user_id: number;
    user_name: string;
    position: number;
    character?: Character;
    is_alive: boolean;
    is_bot: boolean;
    arrow: number;
    bullet: number;
    revealed_identity?: Identity; // SÓ o Xerife aparece aqui
};

// Estado completo da partida vindo do backend
export type GameStateDTO = {
    game_id: string;
    status: "Running" | "Done";
    round_number: number;
    turn_number: number;
    current_player: PublicPlayer;
    current_player_index: number;
    players: PublicPlayer[];
    dice: DiceShowDTO[];
    available_actions: string[];
    winner?: Team;
};

// Dados mostrados em cada face de dado
export type DiceShowDTO = {
    dice: number;
    locked: boolean;
    show: string;
};

// Comandos que o frontend envia ao backend
export type RollDiceCommandDTO = {
    locked_dice_indexes: number[];
};

export type ShootDistanceCommandDTO = {
    distance: string;
    user_bullets: UserBulletsDTO[];
};

export type ExecuteShotsCommandDTO = {
    actor_user_id: number;
    shots_by_distance: ShootDistanceCommandDTO[];
};

export type UserBulletsDTO = {
    user_name: string;
    shots: number;
};

export type CreateGameDTO = {
    player_name: string;
    players_total: number;
};
```

### 1.2 Atualizar `players.ts`

Remover `identity` e `team` do tipo `Player` ou criar `PublicPlayer` separado.
O tipo `Player` legado deve ser removido e substituído por `PublicPlayer`.

```ts
// Antigo (REMOVER):
export type Player = {
    user_name: string;
    position: number;
    user_id: number;
    character: Character | undefined;
    identity: Identity;       // ❌ REMOVER - é interno do backend
    is_alive: boolean;
    is_bot: boolean;
    arrow: number;
    bullet: number;
    team: Team;               // ❌ REMOVER - é interno do backend
};

// Novo (MANTER APENAS ESTE):
export type PublicPlayer = {
    user_id: number;
    user_name: string;
    position: number;
    character?: Character;
    is_alive: boolean;
    is_bot: boolean;
    arrow: number;
    bullet: number;
    revealed_identity?: Identity; // SÓ o Xerife - nunca identidades ocultas
};
```

### 1.3 Remover `game_match.ts`

O tipo `GameDTO` antigo é substituído por `GameStateDTO`. Remover o arquivo ou marcar como deprecated.

---

## 2. Nova Camada de API (`mobile-gun-firing/src/api/`)

### 2.1 Criar `game.ts`

Novo arquivo: `mobile-gun-firing/src/api/game.ts`

```ts
import { api } from "./axios";
import { ResponseDTO } from "../dtos/response";
import {
    GameStateDTO,
    CreateGameDTO,
    RollDiceCommandDTO,
    ExecuteShotsCommandDTO,
} from "../dtos/gameState";

// POST /games - Criar nova partida
export async function createGame(
    command: CreateGameDTO
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameStateDTO>>(
            "/games",
            command
        );
        return response.data.data;
    } catch (error) {
        console.error("Erro ao criar partida:", error);
        throw error;
    }
}

// GET /games/{game_id}/state - Buscar estado público atual
export async function getGameState(
    game_id: string
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.get<ResponseDTO<GameStateDTO>>(
            `/games/${game_id}/state`
        );
        return response.data.data;
    } catch (error) {
        console.error("Erro ao buscar estado:", error);
        throw error;
    }
}

// POST /games/{game_id}/dice/roll - Rolar dados (backend decide os resultados)
export async function rollDice(
    game_id: string,
    command: RollDiceCommandDTO
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameStateDTO>>(
            `/games/${game_id}/dice/roll`,
            command
        );
        return response.data.data;
    } catch (error) {
        console.error("Erro ao rolar dados:", error);
        throw error;
    }
}

// POST /games/{game_id}/actions/shots - Executar tiros do usuário
export async function executeShots(
    game_id: string,
    command: ExecuteShotsCommandDTO
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameStateDTO>>(
            `/games/${game_id}/actions/shots`,
            command
        );
        return response.data.data;
    } catch (error) {
        console.error("Erro ao executar tiros:", error);
        throw error;
    }
}

// POST /games/{game_id}/actions/finish-turn - Passar turno
export async function finishTurn(
    game_id: string
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameStateDTO>>(
            `/games/${game_id}/actions/finish-turn`,
            { actor_user_id: 0 }
        );
        return response.data.data;
    } catch (error) {
        console.error("Erro ao finalizar turno:", error);
        throw error;
    }
}

// POST /games/{game_id}/bot-turn - Executar turno do bot
export async function executeBotTurn(
    game_id: string
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameStateDTO>>(
            `/games/${game_id}/bot-turn`
        );
        return response.data.data;
    } catch (error) {
        console.error("Erro no turno do bot:", error);
        throw error;
    }
}
```

---

## 3. Remover Lógica de Jogo do Frontend

### 3.1 Arquivos para REMOVER ou MARCAR COMO DEPRECATED

| Arquivo | Motivo |
|---------|--------|
| `game/init_game.ts` | Criação de jogadores, identidades e times agora é feita pelo backend via `POST /games` |
| `game/shoot.ts` | Aplicação de tiros (`executeShotInPlayers`, `checkPlayersIsLive`), cálculo de alvos (`players_to_shot`) agora é backend |
| `consts/champion.ts` | Cálculo de campeão (`is_the_champion`) agora é backend. O campo `winner` vem no `GameStateDTO` |
| `game/play_dice.ts` | Rolagem de dados agora é backend via `POST /games/{game_id}/dice/roll` |
| `api/dices.ts` | Endpoints antigos `/dices/valid` e `/dices/execution` são substituídos pelos novos endpoints REST |

### 3.2 Arquivos para ATUALIZAR

#### `components/shotComponent/index.tsx`

**Antes (lógica local):**
- `players_to_shot()` - cálculo de distância para alvos (REMOVIDO)
- `executeShotInPlayers()` - aplicação local de dano (REMOVIDO)
- `checkPlayersIsLive()` - remoção local de mortos (REMOVIDO)
- `tableSituation` - montagem manual da situação (REMOVIDO)
- `botExecuteDices()` - chamada `/dices/execution` (REMOVIDO)
- Vazamento: o componente lê `currentPlayer.identity` e `currentPlayer.team`

**Depois (fluxo novo):**

```tsx
import { executeShots } from "@/src/api/game";
import { GameStateDTO } from "@/src/dtos/gameState";

// O componente deve receber gameState como prop em vez de players/currentPlayer soltos
type ShootProps = {
    isVisible: boolean;
    gameState: GameStateDTO;
    onClose: () => void;
    onStateUpdate: (newState: GameStateDTO) => void;
};

export default function ShotComponent({ isVisible, gameState, onClose, onStateUpdate }: ShootProps) {
    const players = gameState.players;
    const currentPlayer = gameState.current_player;
    const playerMoment = gameState.current_player_index;

    // Calcular alvos usando posições (não identidades!)
    const optionsOneShoot = useMemo(() => {
        return players
            .filter(p => p.is_alive && p.user_id !== currentPlayer.user_id)
            .map(p => p.user_name);
    }, [players, currentPlayer]);

    const [userOneBullets, setUserOneBullets] = useState<UserBulletsDTO[]>([]);

    // Executar tiros: envia comando ao backend, recebe novo estado
    const runExecution = useCallback(async () => {
        const newState = await executeShots(gameState.game_id, {
            actor_user_id: currentPlayer.user_id,
            shots_by_distance: [
                {
                    distance: "1",
                    user_bullets: userOneBullets,
                }
            ],
        });
        if (newState) {
            onStateUpdate(newState);
            setUserOneBullets([]);
            onClose();
        }
    }, [gameState.game_id, currentPlayer.user_id, userOneBullets, onStateUpdate, onClose]);

    // Turno do bot: chama endpoint dedicado
    useEffect(() => {
        if (gameState.status === "Running" && currentPlayer.is_bot && isVisible) {
            executeBotTurn(gameState.game_id).then(newState => {
                if (newState) onStateUpdate(newState);
            });
        }
    }, [currentPlayer.is_bot, isVisible, gameState.game_id, gameState.status]);

    return (
        // ... Renderizar Modal com ListShots igual, mas usando apenas PublicPlayer
        // playersOptions deve ser filtrado apenas por is_alive e user_id != current
    );
}
```

#### `components/executeDicesComponent/index.tsx`

**Antes:** Rola dados localmente com `play_dice()`, gerencia estado local de 3 dados.

**Depois:** Chama `POST /games/{game_id}/dice/roll` com os índices dos dados bloqueados.

```tsx
import { rollDice } from "@/src/api/game";
import { DiceShowDTO, GameStateDTO } from "@/src/dtos/gameState";

type DicesProps = {
    gameState: GameStateDTO;
    onStateUpdate: (newState: GameStateDTO) => void;
};

export default function ExecuteDicesComponent({ gameState, onStateUpdate }: DicesProps) {
    const [lockedIndexes, setLockedIndexes] = useState<number[]>([]);

    const toggleLock = (index: number) => {
        setLockedIndexes(prev =>
            prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
        );
    };

    const rollAllDices = async () => {
        const newState = await rollDice(gameState.game_id, {
            locked_dice_indexes: lockedIndexes,
        });
        if (newState) {
            onStateUpdate(newState);
            setLockedIndexes([]);
        }
    };

    return (
        <View>
            {gameState.dice.map((d, i) => (
                <Pressable key={i} onPress={() => toggleLock(i)}>
                    <Text>
                        {d.locked ? "🔒" : ""} {d.show}
                    </Text>
                </Pressable>
            ))}
            <Pressable onPress={rollAllDices}>
                <Text>Rolar Dados</Text>
            </Pressable>
        </View>
    );
}
```

---

## 4. Fluxo da Tela Principal do Jogo

### 4.1 Página do Jogo (`app/bangMatch/`)

O estado central da tela deve ser um único `GameStateDTO`:

```tsx
const [gameState, setGameState] = useState<GameStateDTO | null>(null);

// Criação da partida: chama POST /games
useEffect(() => {
    createGame({ player_name: "Lucas", players_total: 5 }).then(state => {
        if (state) setGameState(state);
    });
}, []);

// A cada ação (tiro, dado, turno), atualizar o estado com a resposta do backend
const handleStateUpdate = (newState: GameStateDTO) => {
    setGameState(newState);
};
```

**Regras de renderização baseadas no `gameState`:**

| O que mostrar | De onde vem |
|--------------|-------------|
| Se o jogo acabou | `gameState.status === "Done"` |
| Quem ganhou | `gameState.winner` |
| Quem é o jogador atual | `gameState.current_player` |
| Lista de jogadores vivos | `gameState.players.filter(p => p.is_alive)` |
| Dados rolados | `gameState.dice` |
| Quem é o Xerife | `player.revealed_identity === "Xerife"` (SÓ isso!) |
| Ações disponíveis | `gameState.available_actions` |
| Vida, flechas, balas | `player.bullet`, `player.arrow` |

---

## 5. Checklist de Remoção

### Remover do frontend (NUNCA mais acessar):

- [ ] `papel_probability` - nunca existiu no frontend, mas garantir que não seja adicionado
- [ ] `identity` (exceto `revealed_identity` que só mostra o Xerife)
- [ ] `team`
- [ ] Cálculo de campeão (`is_the_champion` de `consts/champion.ts`)
- [ ] Aplicação local de tiro (`executeShotInPlayers`, `checkPlayersIsLive`)
- [ ] Cálculo de alvos por distância (`players_to_shot`)
- [ ] Criação de jogadores (`create_players` de `game/init_game.ts`)
- [ ] Montagem de `action_history` no frontend
- [ ] Montagem de `table_situation` manual
- [ ] Chamada a `/dices/execution` (endpoint antigo)

### Arquivos para deletar:

- [ ] `game/init_game.ts`
- [ ] `game/shoot.ts`
- [ ] `game/play_dice.ts`
- [ ] `game/dices_analyzer.ts`
- [ ] `consts/champion.ts`
- [ ] `consts/characters.ts` (ou manter apenas para referência visual, sem usar `initial_bullet`)
- [ ] `api/dices.ts`

### Arquivos para atualizar:

- [ ] `dtos/players.ts` - substituir `Player` por `PublicPlayer`
- [ ] `components/shotComponent/index.tsx` - remover lógica local, usar API
- [ ] `components/executeDicesComponent/index.tsx` - remover rolagem local, usar API
- [ ] `app/bangMatch/*` - usar `GameStateDTO` como estado central
- [ ] `components/cardPlayer/` - mostrar apenas `revealed_identity`, não `identity`

---

## 6. Exemplo de Uso Completo

```tsx
// Exemplo de fluxo completo na tela do jogo
import { createGame, executeShots, executeBotTurn, finishTurn, rollDice } from "@/src/api/game";
import { GameStateDTO } from "@/src/dtos/gameState";

function BangMatchScreen() {
    const [gameState, setGameState] = useState<GameStateDTO | null>(null);
    const [loading, setLoading] = useState(false);

    // 1. Criar partida
    useEffect(() => {
        createGame({ player_name: "Lucas", players_total: 5 })
            .then(setGameState)
            .catch(console.error);
    }, []);

    // 2. Função genérica para atualizar estado após ação
    const handleAction = async (action: () => Promise<GameStateDTO | undefined>) => {
        setLoading(true);
        const newState = await action();
        if (newState) setGameState(newState);
        setLoading(false);
    };

    if (!gameState) return <LoadingScreen />;

    const { status, current_player, players, winner, available_actions, dice } = gameState;

    // 3. Verificar se o jogo acabou
    if (status === "Done") {
        return <WinnerScreen winner={winner!} />;
    }

    // 4. Se o jogador atual é um bot, executar turno automaticamente
    if (current_player.is_bot) {
        return (
            <BotTurnScreen
                player={current_player}
                onComplete={() => handleAction(() => executeBotTurn(gameState.game_id))}
            />
        );
    }

    // 5. Interface para jogador humano
    return (
        <View>
            <Text>Turno de: {current_player.user_name}</Text>
            <Text>Vida: {current_player.bullet}</Text>

            {/* Dados */}
            <DiceComponent
                dice={dice}
                onRoll={(lockedIndexes) =>
                    handleAction(() => rollDice(gameState.game_id, { locked_dice_indexes: lockedIndexes }))
                }
            />

            {/* Tiros */}
            {available_actions.includes("SHOOT") && (
                <ShotComponent
                    gameState={gameState}
                    onShoot={(command) =>
                        handleAction(() => executeShots(gameState.game_id, command))
                    }
                />
            )}

            {/* Passar turno */}
            {available_actions.includes("FINISH_TURN") && (
                <Button
                    title="Passar Turno"
                    onPress={() => handleAction(() => finishTurn(gameState.game_id))}
                />
            )}
        </View>
    );
}
```

---

## 7. Contratos de Confiança

### O que o frontend NUNCA deve fazer:
- Calcular quem está a distância 1 ou 2 (backend decide alvos disponíveis)
- Aplicar dano nos jogadores (backend aplica e retorna novo estado)
- Remover jogadores mortos (backend remove e retorna nova lista)
- Decidir quem ganhou (backend resolve e retorna `winner`)
- Montar `action_history` para enviar ao backend
- Ler `identity` de qualquer jogador (exceto `revealed_identity` do Xerife)
- Usar `papel_probability` para qualquer decisão

### O que o frontend DEVE fazer:
- Enviar comandos de ação (`RollDiceCommandDTO`, `ExecuteShotsCommandDTO`)
- Receber `GameStateDTO` como resposta de CADA ação
- Atualizar a UI inteira baseada apenas no `GameStateDTO` recebido
- Renderizar `revealed_identity` apenas quando não for `null` (mostra o Xerife)
- Chamar `executeBotTurn()` quando `current_player.is_bot === true`

---

## 8. Migração Incremental (Sugestão)

Para não quebrar o jogo de uma vez, migrar em etapas:

1. **Etapa 1:** Criar `gameState.ts` com os novos tipos e `api/game.ts` com os endpoints
2. **Etapa 2:** Na tela do jogo, fazer a criação de partida via `POST /games` e armazenar `GameStateDTO`
3. **Etapa 3:** Substituir a rolagem de dados local pelo endpoint `POST /games/{game_id}/dice/roll`
4. **Etapa 4:** Substituir a aplicação de tiros pelo endpoint `POST /games/{game_id}/actions/shots`
5. **Etapa 5:** Substituir o turno do bot pelo endpoint `POST /games/{game_id}/bot-turn`
6. **Etapa 6:** Remover cálculo de campeão local, usar `gameState.winner`
7. **Etapa 7:** Remover `Player` antigo, migrar tudo para `PublicPlayer`
8. **Etapa 8:** Deletar arquivos obsoletos (`game/init_game.ts`, `game/shoot.ts`, etc.)
9. **Etapa 9:** Remover chamadas antigas (`api/dices.ts`, `/dices/execution`)

---

## 9. Resumo das Mudanças nos Endpoints

| Antigo (Frontend) | Novo (Backend) |
|-------------------|----------------|
| `create_players()` local | `POST /games` |
| `play_dice()` local | `POST /games/{game_id}/dice/roll` |
| `executeShotInPlayers()` local | `POST /games/{game_id}/actions/shots` |
| `checkPlayersIsLive()` local | (automático no backend após tiro) |
| `is_the_champion()` local | `gameState.winner` |
| `POST /dices/execution` (para bot) | `POST /games/{game_id}/bot-turn` |
| Montagem manual de `action_history` | (backend gera automaticamente) |
| Montagem manual de `table_situation` | (backend monta contexto interno) |
