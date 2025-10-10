import { isAxiosError } from "axios";

import { ResponseDTO } from "../dtos/response";
import { api } from "./axios";
import { CreateGameDTO } from "../dtos/game_match";

export async function createGame(
    game: CreateGameDTO
): Promise<any | undefined> {
    try {
        const response = await api.post<ResponseDTO<CreateGameDTO>>(
            "/match_game",
            game
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
