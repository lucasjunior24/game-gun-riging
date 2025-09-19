import { isAxiosError } from "axios";
import { DiceCombination, ExecuteDicesDTO } from "../dtos/dice";
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

export async function executeDices(
    execution: ExecuteDicesDTO
): Promise<ExecuteDicesDTO | undefined> {
    try {
        const response = await api.put<ResponseDTO<ExecuteDicesDTO>>(
            "/dices/execution",
            execution
        );
        // console.log(response);
        return response.data.data;
    } catch (error) {
        if (isAxiosError(error)) {
            console.log(error.message);
            console.log(error);
            // console.log(error.code);
        } else {
            console.error(error);
        }
    }
}
