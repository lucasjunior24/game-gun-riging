import { die, gameView } from "../../test/fixtures";
import {
    canConfirm,
    initialTurnUi,
    toAssignments,
    turnReducer,
    turnStage,
} from "../turnReducer";

const rerollView = gameView({
    rolls_left: 2,
    allowed_actions: ["ROLL", "STOP_ROLLING"],
    dice: [
        die({ index: 0, face: "Dinamite", locked: true, can_reroll: false }),
        die({ index: 1, face: "Flecha", can_reroll: true }),
        die({ index: 2, face: "1", can_reroll: true }),
        die({ index: 3, face: "Cerveja", can_reroll: true }),
        die({ index: 4, face: "Metralhadora", can_reroll: true }),
    ],
});

const resolveView = gameView({
    phase: "RESOLVENDO",
    rolls_left: 0,
    allowed_actions: ["RESOLVE"],
    dice: [
        die({ index: 0, face: "1", valid_target_user_ids: [2, 5] }),
        die({ index: 1, face: "Cerveja", valid_target_user_ids: [1, 2, 3, 4, 5] }),
        die({ index: 2, face: "Flecha" }),
        die({ index: 3, face: "Dinamite", locked: true }),
        die({ index: 4, face: "2", resolved: true }),
    ],
});

describe("turnReducer", () => {
    it("não marca Dinamite para rolar de novo", () => {
        const state = turnReducer(initialTurnUi, { type: "TOGGLE_REROLL", index: 0 }, rerollView);
        expect(state.rerollMarked).toEqual([]);
    });

    it("marca e desmarca dados que podem rolar de novo", () => {
        let state = turnReducer(initialTurnUi, { type: "TOGGLE_REROLL", index: 1 }, rerollView);
        state = turnReducer(state, { type: "TOGGLE_REROLL", index: 2 }, rerollView);
        expect(state.rerollMarked).toEqual([1, 2]);
        state = turnReducer(state, { type: "TOGGLE_REROLL", index: 1 }, rerollView);
        expect(state.rerollMarked).toEqual([2]);
    });

    it("não aceita alvo fora de valid_target_user_ids", () => {
        let state = turnReducer(initialTurnUi, { type: "SELECT_DIE", index: 0 }, resolveView);
        state = turnReducer(state, { type: "ASSIGN", targetUserId: 3 }, resolveView);
        expect(state.assignments).toEqual({});
        expect(state.selectedDie).toBe(0);
    });

    it("não seleciona dado que não está pendente", () => {
        for (const index of [2, 3, 4]) {
            const state = turnReducer(initialTurnUi, { type: "SELECT_DIE", index }, resolveView);
            expect(state.selectedDie).toBeNull();
        }
    });

    it("atribui e já seleciona o próximo dado pendente", () => {
        let state = turnReducer(initialTurnUi, { type: "SELECT_DIE", index: 0 }, resolveView);
        state = turnReducer(state, { type: "ASSIGN", targetUserId: 5 }, resolveView);
        expect(state.assignments).toEqual({ 0: 5 });
        expect(state.selectedDie).toBe(1);
    });

    it("Confirmar só fica liberado com todos os pendentes atribuídos", () => {
        let state = turnReducer(initialTurnUi, { type: "SELECT_DIE", index: 0 }, resolveView);
        state = turnReducer(state, { type: "ASSIGN", targetUserId: 2 }, resolveView);
        expect(canConfirm(state, resolveView)).toBe(false);

        state = turnReducer(state, { type: "ASSIGN", targetUserId: 1 }, resolveView);
        expect(canConfirm(state, resolveView)).toBe(true);
        expect(toAssignments(state)).toEqual([
            { dice_index: 0, target_user_id: 2 },
            { dice_index: 1, target_user_id: 1 },
        ]);
    });

    it("RESET volta ao estado inicial", () => {
        const state = turnReducer(initialTurnUi, { type: "TOGGLE_REROLL", index: 1 }, rerollView);
        expect(turnReducer(state, { type: "RESET" }, rerollView)).toEqual(initialTurnUi);
    });
});

describe("turnStage", () => {
    it("segue o allowed_actions do servidor", () => {
        expect(turnStage(gameView({ allowed_actions: ["ROLL"] }))).toBe("PODE_ROLAR");
        expect(turnStage(rerollView)).toBe("ESCOLHENDO_REROLL");
        expect(turnStage(resolveView)).toBe("ATRIBUINDO_DADOS");
        expect(turnStage(gameView({ allowed_actions: ["FINISH_TURN"] }))).toBe("ENCERRANDO");
        expect(turnStage(gameView({ allowed_actions: ["WAIT_BOTS"] }))).toBe("ESPERANDO_BOTS");
        expect(turnStage(gameView({ status: "Done", allowed_actions: [] }))).toBe("FIM");
    });

    it("sem ROLL não existe quarta rolagem", () => {
        const view = gameView({ rolls_left: 0, allowed_actions: ["STOP_ROLLING"] });
        expect(view.allowed_actions).not.toContain("ROLL");
        expect(turnStage(view)).toBe("ESCOLHENDO_REROLL");
    });
});
