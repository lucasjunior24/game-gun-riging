import {
    CreateGameDTO,
    ExecuteShotsCommandDTO,
    GameStateDTO,
    RollDiceCommandDTO,
} from "../dtos/gameState";
import { ResponseDTO } from "../dtos/response";
import { api } from "./axios";

// POST /games - Criar nova partida
export async function createGame(
    command: CreateGameDTO,
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameStateDTO>>(
            "/games",
            command,
        );
        return response.data.data;
    } catch (error) {
        console.error("Erro ao criar partida:", error);
        throw error;
    }
}

// GET /games/{game_id}/state - Buscar estado público atual
export async function getGameState(
    game_id: string,
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.get<ResponseDTO<GameStateDTO>>(
            `/games/${game_id}/state`,
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
    command: RollDiceCommandDTO,
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameStateDTO>>(
            `/games/${game_id}/dice/roll`,
            command,
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
    command: ExecuteShotsCommandDTO,
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameStateDTO>>(
            `/games/${game_id}/actions/shots`,
            command,
        );
        return response.data.data;
    } catch (error) {
        console.error("Erro ao executar tiros:", error);
        throw error;
    }
}

// POST /games/{game_id}/actions/finish-turn - Passar turno
export async function finishTurn(
    game_id: string,
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameStateDTO>>(
            `/games/${game_id}/actions/finish-turn`,
            { actor_user_id: 0 },
        );
        return response.data.data;
    } catch (error) {
        console.error("Erro ao finalizar turno:", error);
        throw error;
    }
}

// POST /games/{game_id}/bot-turn - Executar turno do bot
export async function executeBotTurn(
    game_id: string,
): Promise<GameStateDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameStateDTO>>(
            `/games/${game_id}/bot-turn`,
        );
        return response.data.data;
    } catch (error) {
        console.error("Erro no turno do bot:", error);
        throw error;
    }
}
