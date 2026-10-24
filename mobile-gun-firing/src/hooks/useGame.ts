// Único dono das chamadas à API da partida. Guarda a visão do servidor, a versão,
// o cursor de eventos e a fila de animação. Nenhuma regra do jogo mora aqui.
import { useCallback, useEffect, useRef, useState } from "react";

import * as gameApi from "../api/game";
import { Assignment, GameView } from "../dtos/gameView";
import { AnimationStep, playSteps, toAnimationSteps } from "../game/eventQueue";
import { isBotTurn } from "../game/turnReducer";

type Session = { gameId: string; userId: number };

// Sobrevive a sair e voltar da tela: ao remontar, busca o estado em vez de criar outra partida
let savedSession: Session | null = null;

export function resetSavedSession() {
    savedSession = null;
}

export type UseGameOptions = {
    playersTotal?: number;
};

export function useGame(playerName: string, { playersTotal = 5 }: UseGameOptions = {}) {
    const [view, setView] = useState<GameView | null>(null);
    const [animating, setAnimating] = useState<AnimationStep | null>(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const viewRef = useRef<GameView | null>(null);
    const inFlight = useRef(false);
    const lastEventId = useRef(0);
    const skip = useRef(false);

    const commit = useCallback((next: GameView) => {
        lastEventId.current = next.last_event_id;
        viewRef.current = next;
        setView(next);
    }, []);

    // Toda ação de jogo passa por aqui: no máximo uma em voo, e o finally sempre destrava.
    const run = useCallback(
        async (call: (v: GameView) => Promise<GameView>) => {
            const current = viewRef.current;
            if (inFlight.current || !current) return;
            inFlight.current = true;
            setBusy(true);
            setError(null);
            let result: GameView | null = null;
            try {
                const next = await call(current);
                await playSteps(toAnimationSteps(next.events, next), setAnimating, () => skip.current);
                result = next;
            } catch (e) {
                // 409: outra chamada já mudou o estado. Outros erros: mostra e ressincroniza.
                if (!gameApi.isConflict(e)) setError(gameApi.errorMessage(e));
                try {
                    result = await gameApi.getState(
                        current.game_id,
                        current.me.user_id,
                        lastEventId.current,
                    );
                } catch (refreshError) {
                    setError(gameApi.errorMessage(refreshError));
                }
            } finally {
                skip.current = false;
                setAnimating(null);
                setBusy(false);
                inFlight.current = false;
            }
            // Depois de destravar: a nova versão pode disparar o efeito dos bots
            if (result) commit(result);
        },
        [commit],
    );

    const start = useCallback(async () => {
        if (inFlight.current) return;
        inFlight.current = true;
        setBusy(true);
        setError(null);
        let result: GameView | null = null;
        try {
            if (!savedSession) {
                const created = await gameApi.createGame({
                    player_name: playerName,
                    players_total: playersTotal,
                    shuffle_roles: true,
                });
                const human = created.players.find((p) => !p.is_bot) ?? created.players[0];
                savedSession = { gameId: created.game_id, userId: human.user_id };
            }
            result = await gameApi.getState(savedSession.gameId, savedSession.userId);
        } catch (e) {
            setError(gameApi.errorMessage(e));
            savedSession = null; // partida sumiu (ex.: servidor reiniciou): a próxima tentativa cria outra
        } finally {
            setBusy(false);
            inFlight.current = false;
        }
        if (result) commit(result);
    }, [commit, playerName, playersTotal]);

    const started = useRef(false);
    useEffect(() => {
        if (started.current) return;
        started.current = true;
        start();
    }, [start]);

    const advanceBots = useCallback(
        () =>
            run((v) =>
                gameApi.advanceBots(v.game_id, {
                    expected_version: v.version,
                    since_event_id: lastEventId.current,
                }),
            ),
        [run],
    );

    // Bots jogam quando o estado diz que é a vez deles. Depende só da versão:
    // cada versão nova dispara no máximo uma chamada (inFlight e o 409 cobrem o resto).
    const version = view?.version;
    const botTurn = view ? isBotTurn(view) : false;
    useEffect(() => {
        if (version !== undefined && botTurn) advanceBots();
    }, [version, botTurn, advanceBots]);

    const command = (v: GameView) => ({
        actor_user_id: v.me.user_id,
        expected_version: v.version,
    });

    return {
        view,
        animating,
        busy,
        error,
        roll: (rerollIndexes: number[]) =>
            run((v) => gameApi.roll(v.game_id, { ...command(v), reroll_indexes: rerollIndexes })),
        stopRolling: () => run((v) => gameApi.stopRolling(v.game_id, command(v))),
        resolve: (assignments: Assignment[]) =>
            run((v) => gameApi.resolve(v.game_id, { ...command(v), assignments })),
        finishTurn: () => run((v) => gameApi.finishTurn(v.game_id, command(v))),
        advanceBots,
        skipAnimation: () => {
            skip.current = true;
        },
        // Sem partida: tenta criar de novo. Com partida: na vez dos bots tenta avançar,
        // senão só ressincroniza com o servidor.
        retry: () => {
            const current = viewRef.current;
            if (!current) return start();
            if (isBotTurn(current)) return advanceBots();
            return run((v) => gameApi.getState(v.game_id, v.me.user_id, lastEventId.current));
        },
        newGame: () => {
            if (inFlight.current) return;
            savedSession = null;
            viewRef.current = null;
            lastEventId.current = 0;
            setView(null);
            start();
        },
    };
}
