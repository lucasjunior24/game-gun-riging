import { event, gameView, player } from "../../test/fixtures";
import { DURATION_MS, playSteps, toAnimationSteps } from "../eventQueue";

const view = gameView({
    players: [
        player({ user_id: 1, user_name: "Lucas" }),
        player({ user_id: 2, user_name: "Murilo" }),
    ],
});

describe("toAnimationSteps", () => {
    it("cada tipo conhecido vira um passo com texto e duração", () => {
        const types = Object.keys(DURATION_MS);
        const steps = toAnimationSteps(
            types.map((type, i) =>
                event({ id: i + 1, type, actor_user_id: 2, target_user_id: 1, amount: 1 }),
            ),
            view,
        );
        expect(steps).toHaveLength(types.length);
        for (const step of steps) {
            expect(step.text.length).toBeGreaterThan(0);
            expect(step.durationMs).toBe(DURATION_MS[step.event.type]);
        }
    });

    it("usa os nomes e trata o próprio jogador como você", () => {
        const [shot] = toAnimationSteps(
            [event({ type: "TIRO", actor_user_id: 2, target_user_id: 1 })],
            view,
        );
        expect(shot.text).toBe("Murilo atirou em você 🔫");
    });

    it("mostra o papel revelado na morte", () => {
        const [death] = toAnimationSteps(
            [event({ type: "MORTE", target_user_id: 2, target_public_identity: "Renegado" })],
            view,
        );
        expect(death.text).toContain("Renegado");
    });

    it("ignora eventos desconhecidos sem quebrar", () => {
        const steps = toAnimationSteps(
            [event({ id: 1, type: "NOVO_TIPO" }), event({ id: 2, type: "FLECHA", actor_user_id: 2 })],
            view,
        );
        expect(steps.map((s) => s.event.id)).toEqual([2]);
    });
});

describe("playSteps", () => {
    beforeEach(() => jest.useFakeTimers());
    afterEach(() => jest.useRealTimers());

    it("mostra um passo por vez e limpa no fim", async () => {
        const steps = toAnimationSteps(
            [event({ id: 1, type: "TIRO" }), event({ id: 2, type: "DANO" })],
            view,
        );
        const shown: (number | null)[] = [];
        const done = playSteps(steps, (s) => shown.push(s ? s.event.id : null));
        await jest.runAllTimersAsync();
        await done;
        expect(shown).toEqual([1, 2, null]);
    });

    it("pular encerra a fila", async () => {
        const steps = toAnimationSteps(
            [event({ id: 1, type: "TIRO" }), event({ id: 2, type: "DANO" })],
            view,
        );
        let skipped = false;
        const shown: (number | null)[] = [];
        const done = playSteps(
            steps,
            (s) => {
                shown.push(s ? s.event.id : null);
                skipped = true;
            },
            () => skipped,
        );
        await jest.runAllTimersAsync();
        await done;
        expect(shown).toEqual([1, null]);
    });
});
