import { DiceCombination } from "../consts/dice";
import { ResponseDTO } from "../dtos/response";
import { api } from "./axios";

export async function validDices(
    dices: DiceCombination[]
): Promise<DiceCombination[] | undefined> {
    try {
        const response = await api.put<ResponseDTO<DiceCombination[]>>(
            "/dices/valid",
            dices
        );
        return response.data.data;
    } catch (error) {
        console.error(error);
    }
}
