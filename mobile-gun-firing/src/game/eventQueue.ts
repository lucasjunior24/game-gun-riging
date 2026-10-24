// Converte eventos do servidor em passos de animação. A lógica já foi resolvida no
// servidor: aqui o tempo só controla o desenho.
import { faceIcon } from "../consts/diceFaces";
import { GameEvent, GameView } from "../dtos/gameView";

export type AnimationStep = {
    event: GameEvent;
    text: string;
    durationMs: number;
};

// DADO_ROLADO é curto de propósito: uma rodada de bots gera dezenas deles
export const DURATION_MS: Record<string, number> = {
    TURNO_INICIADO: 700,
    DADO_ROLADO: 150,
    FLECHA: 500,
    ATAQUE_INDIGENA: 1400,
    DINAMITE: 1400,
    TIRO: 900,
    CERVEJA: 800,
    GATLING: 1400,
    DANO: 500,
    MORTE: 1600,
    VITORIA: 1600,
};

type Names = (userId: number | null) => string;

const TEXT: Record<string, (e: GameEvent, name: Names, meId: number) => string> = {
    TURNO_INICIADO: (e, name, meId) =>
        e.actor_user_id === meId ? "Sua vez!" : `Vez de ${name(e.actor_user_id)}`,
    DADO_ROLADO: (e, name) => `${name(e.actor_user_id)} rolou ${faceIcon(String(e.data.face ?? ""))}`,
    FLECHA: (e, name) => `${name(e.actor_user_id)} pegou uma flecha 🏹`,
    ATAQUE_INDIGENA: () => "Ataque indígena! 🪶",
    DINAMITE: (e, name) => `3 Dinamites! ${name(e.actor_user_id)} se explodiu 🧨`,
    TIRO: (e, name) => `${name(e.actor_user_id)} atirou em ${name(e.target_user_id)} 🔫`,
    CERVEJA: (e, name) =>
        `${name(e.actor_user_id)} deu cerveja para ${name(e.target_user_id)} 🍺 (+${e.amount})`,
    GATLING: (e, name) => `${name(e.actor_user_id)} disparou a Gatling! 💥`,
    DANO: (e, name) => `${name(e.target_user_id)} perdeu ${e.amount} de vida`,
    MORTE: (e, name) =>
        `${name(e.target_user_id)} morreu ☠️` +
        (e.target_public_identity ? ` — era ${e.target_public_identity}` : ""),
    VITORIA: (e) => `Fim de jogo: vitória de ${String(e.data.winner ?? "?")} 🏆`,
};

export function toAnimationSteps(
    events: GameEvent[],
    view: Pick<GameView, "players" | "me">,
): AnimationStep[] {
    const byId = new Map(view.players.map((p) => [p.user_id, p.user_name]));
    const name: Names = (userId) => {
        if (userId === null || userId === undefined) return "?";
        if (userId === view.me.user_id) return "você";
        return byId.get(userId) ?? `Jogador ${userId}`;
    };

    const steps: AnimationStep[] = [];
    for (const event of events) {
        const toText = TEXT[event.type];
        if (!toText) continue; // tipo desconhecido: ignora sem quebrar
        const text = toText(event, name, view.me.user_id);
        steps.push({
            event,
            text: text.charAt(0).toUpperCase() + text.slice(1),
            durationMs: DURATION_MS[event.type],
        });
    }
    return steps;
}

const TICK_MS = 50;

function wait(ms: number, skipped: () => boolean): Promise<void> {
    return new Promise((resolve) => {
        let elapsed = 0;
        const tick = () => {
            if (skipped() || elapsed >= ms) return resolve();
            elapsed += TICK_MS;
            setTimeout(tick, Math.min(TICK_MS, ms));
        };
        tick();
    });
}

/** Mostra um passo por vez. `skipped` encerra a fila na hora (botão "pular"). */
export async function playSteps(
    steps: AnimationStep[],
    onStep: (step: AnimationStep | null) => void,
    skipped: () => boolean = () => false,
): Promise<void> {
    for (const step of steps) {
        if (skipped()) break;
        onStep(step);
        await wait(step.durationMs, skipped);
    }
    onStep(null);
}
