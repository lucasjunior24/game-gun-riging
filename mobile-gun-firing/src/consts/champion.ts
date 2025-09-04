import { Team } from "../dtos/characters";
import { Player } from "../dtos/players";

export function is_the_champion(livePlayers: Player[]): Team | undefined {
    const xerife = livePlayers.find((p) => p.identity === "Xerife");
    const outlaws = livePlayers.filter((p) => p.team === "Fora da lei");
    const renegade = livePlayers.filter((p) => p.identity === "Renegado");

    if (
        xerife === undefined &&
        renegade.length === 1 &&
        livePlayers.length === 1
    ) {
        return "Renegado";
    } else if (xerife && outlaws.length === 0 && renegade.length === 0) {
        return "Xerife";
    } else if (livePlayers.length && xerife === undefined) {
        return "Fora da lei";
    }
    return undefined;
}
