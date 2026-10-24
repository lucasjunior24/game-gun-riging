import { isAxiosError } from "axios";

import { CreateGameDTO, GameStateDTO } from "../dtos/gameState";
import {
    AdvanceBotsCommand,
    Command,
    GameView,
    ResolveCommand,
    RollCommand,
} from "../dtos/gameView";
import { ResponseDTO } from "../dtos/response";
import { api } from "./axios";

// Os erros sobem para o useGame, que decide o que fazer (409 -> buscar o estado).

// POST /games - Criar nova partida (ainda devolve o formato antigo)
export async function createGame(command: CreateGameDTO): Promise<GameStateDTO> {
    const response = await api.post<ResponseDTO<GameStateDTO>>("/games", command);
    return response.data.data;
}

// GET /games/{game_id}/state - Visão do jogador
export async function getState(
    game_id: string,
    viewer_user_id: number,
    since_event_id?: number,
): Promise<GameView> {
    const response = await api.get<ResponseDTO<GameView>>(
        `/games/${game_id}/state`,
        { params: { viewer_user_id, since_event_id } },
    );
    return response.data.data;
}

// POST /games/{game_id}/roll - Primeira rolagem (todos) ou rolar de novo os marcados
export async function roll(game_id: string, command: RollCommand): Promise<GameView> {
    const response = await api.post<ResponseDTO<GameView>>(
        `/games/${game_id}/roll`,
        command,
    );
    return response.data.data;
}

// POST /games/{game_id}/stop-rolling - Parar de rolar e ir para a resolução
export async function stopRolling(game_id: string, command: Command): Promise<GameView> {
    const response = await api.post<ResponseDTO<GameView>>(
        `/games/${game_id}/stop-rolling`,
        command,
    );
    return response.data.data;
}

// POST /games/{game_id}/resolve - Um alvo para cada dado de 1, 2 e Cerveja
export async function resolve(
    game_id: string,
    command: ResolveCommand,
): Promise<GameView> {
    const response = await api.post<ResponseDTO<GameView>>(
        `/games/${game_id}/resolve`,
        command,
    );
    return response.data.data;
}

// POST /games/{game_id}/finish-turn - Encerrar turno sem dados pendentes
export async function finishTurn(game_id: string, command: Command): Promise<GameView> {
    const response = await api.post<ResponseDTO<GameView>>(
        `/games/${game_id}/finish-turn`,
        command,
    );
    return response.data.data;
}

// POST /games/{game_id}/bots/advance - Joga os bots até a vez do humano
export async function advanceBots(
    game_id: string,
    command: AdvanceBotsCommand,
): Promise<GameView> {
    const response = await api.post<ResponseDTO<GameView>>(
        `/games/${game_id}/bots/advance`,
        command,
    );
    return response.data.data;
}

export function isConflict(error: unknown): boolean {
    return isAxiosError(error) && error.response?.status === 409;
}

export function errorMessage(error: unknown): string {
    if (isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        if (typeof detail === "string") return detail;
        return error.message;
    }
    return error instanceof Error ? error.message : String(error);
}
