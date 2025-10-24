import { isAxiosError } from "axios";

import { ResponseDTO } from "../dtos/response";
import { api } from "./axios";
import { CreateGameDTO, GameDTO } from "../dtos/game_match";

export async function createGame(
    game: CreateGameDTO
): Promise<GameDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameDTO>>(
            "/match_game",
            game
        );
        // console.log(response.data.data, " Teste ");
        return response.data.data;
    } catch (error) {
        if (isAxiosError(error)) {
            // console.log(error.response?.data);
            console.error("Error Request: ", error.message);
        } else {
            console.error(error);
        }
    }
}

export async function finisheGame(
    game_id: string
): Promise<GameDTO | undefined> {
    try {
        const response = await api.post<ResponseDTO<GameDTO>>(
            `/match_game/status?id=${game_id}`
        );
        console.log(response.data.data, " Teste ");
        return response.data.data;
    } catch (error) {
        if (isAxiosError(error)) {
            // console.log(error.response?.data);
            console.error(error);
        } else {
            console.error(error);
        }
    }
}
