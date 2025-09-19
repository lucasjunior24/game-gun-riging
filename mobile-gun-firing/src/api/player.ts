import { isAxiosError } from "axios";
import { Player } from "../dtos/players";
import { ResponseDTO } from "../dtos/response";
import { api } from "./axios";

export async function createPlayer(
    player: Player
): Promise<Player | undefined> {
    try {
        const response = await api.post<ResponseDTO<Player>>("/player", player);
        // console.log(response.data.data);
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
