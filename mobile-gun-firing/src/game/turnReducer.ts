// Estado de interface do turno do humano. Função pura: (estado, ação, visão) => novo estado.
// Só usa o que o servidor mandou (can_reroll, valid_target_user_ids); não calcula distância.
import { Assignment, GameView } from "../dtos/gameView";

export type TurnUi = {
    rerollMarked: number[];
    selectedDie: number | null;
    assignments: Record<number, number>; // dice_index -> target_user_id
};

export type TurnAction =
    | { type: "TOGGLE_REROLL"; index: number }
    | { type: "SELECT_DIE"; index: number }
    | { type: "ASSIGN"; targetUserId: number }
    | { type: "RESET" };

export const initialTurnUi: TurnUi = {
    rerollMarked: [],
    selectedDie: null,
    assignments: {},
};

export type TurnStage =
    | "ESPERANDO_BOTS"
    | "PODE_ROLAR"
    | "ESCOLHENDO_REROLL"
    | "ATRIBUINDO_DADOS"
    | "ENCERRANDO"
    | "FIM";

export function turnStage(view: GameView): TurnStage {
    if (view.status === "Done") return "FIM";
    const actions = view.allowed_actions;
    // STOP_ROLLING só aparece depois da primeira rolagem
    if (actions.includes("ROLL") && !actions.includes("STOP_ROLLING")) return "PODE_ROLAR";
    if (actions.includes("STOP_ROLLING")) return "ESCOLHENDO_REROLL";
    if (actions.includes("RESOLVE")) return "ATRIBUINDO_DADOS";
    if (actions.includes("FINISH_TURN")) return "ENCERRANDO";
    return "ESPERANDO_BOTS";
}

export function isBotTurn(view: GameView): boolean {
    return view.status === "Running" && view.allowed_actions.includes("WAIT_BOTS");
}

/** Dados de 1, 2 e Cerveja que ainda precisam de alvo. */
export function pendingDice(view: GameView): number[] {
    return view.dice
        .filter((d) => !d.resolved && d.valid_target_user_ids.length > 0)
        .map((d) => d.index);
}

export function canConfirm(state: TurnUi, view: GameView): boolean {
    const pending = pendingDice(view);
    return pending.length > 0 && pending.every((i) => state.assignments[i] !== undefined);
}

export function canReroll(state: TurnUi, view: GameView): boolean {
    return view.allowed_actions.includes("ROLL") && state.rerollMarked.length > 0;
}

export function toAssignments(state: TurnUi): Assignment[] {
    return Object.entries(state.assignments).map(([index, target]) => ({
        dice_index: Number(index),
        target_user_id: target,
    }));
}

/** Jogadores que acendem na mesa: os alvos válidos do dado selecionado. */
export function highlightedTargets(state: TurnUi, view: GameView): number[] {
    if (state.selectedDie === null) return [];
    return view.dice[state.selectedDie]?.valid_target_user_ids ?? [];
}

export function turnReducer(state: TurnUi, action: TurnAction, view: GameView): TurnUi {
    switch (action.type) {
        case "TOGGLE_REROLL": {
            const die = view.dice[action.index];
            if (!die?.can_reroll) return state; // Dinamite ou fora da fase: ignora
            const marked = state.rerollMarked.includes(action.index)
                ? state.rerollMarked.filter((i) => i !== action.index)
                : [...state.rerollMarked, action.index];
            return { ...state, rerollMarked: marked };
        }
        case "SELECT_DIE": {
            if (!pendingDice(view).includes(action.index)) return state;
            const selectedDie = state.selectedDie === action.index ? null : action.index;
            return { ...state, selectedDie };
        }
        case "ASSIGN": {
            if (state.selectedDie === null) return state;
            const valid = view.dice[state.selectedDie].valid_target_user_ids;
            if (!valid.includes(action.targetUserId)) return state; // só alvos que o servidor permitiu
            const assignments = {
                ...state.assignments,
                [state.selectedDie]: action.targetUserId,
            };
            // Já seleciona o próximo dado sem alvo, para o jogador só tocar nos jogadores
            const next = pendingDice(view).find((i) => assignments[i] === undefined);
            return { ...state, assignments, selectedDie: next ?? null };
        }
        case "RESET":
            return initialTurnUi;
        default:
            return state;
    }
}
