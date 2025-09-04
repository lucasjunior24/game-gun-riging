import { Player } from "../dtos/players";

export function shoot_to_the_right(
    player_moment: number,
    size: number,
    distance: number
): number {
    if (size === Number(player_moment)) {
        return distance;
    } else if (Number(player_moment) + distance > size) {
        const total = Number(player_moment) + distance;

        return total - size;
    }

    return Number(player_moment) + distance;
}
export function shoot_to_the_left(
    player_moment: number,
    size: number,
    distance: number
): number {
    if (size === player_moment) {
        return size - distance;
    } else if (player_moment < size) {
        const total = player_moment - distance;
        if (total > 0) {
            return total;
        }
        if (total < 0) {
            const total = distance - Number(player_moment);
            return size - total;
        }
        return size - total;
    }

    return Number(player_moment) - distance;
}

export function players_to_shot(
    current_player: number,
    total_players: number,
    dice: 1 | 2
) {
    const one_short_right = shoot_to_the_right(
        current_player,
        total_players,
        dice
    );
    const one_short_left = shoot_to_the_left(
        current_player,
        total_players,
        dice
    );
    const players = new Set([one_short_left - 1, one_short_right - 1]);
    const playersArray = Array.from(players);
    return playersArray;
}

export function definirTiros(
    state: number,
    playerName: string,
    players: Player[],
    playerShotedName: string,
    shotTotal: number,
    handleSetPlayers: (players: Player[]) => void,
    handleSetPlayer: (playerMoment: number) => void
): number {
    if (state > 0) {
        const new_players = players
            .map((p) => {
                if (p.user_name === playerShotedName && p.bullet) {
                    p.bullet -= shotTotal;
                    if (p.bullet < 1) {
                        return;
                    }
                    return p;
                }
                return p;
            })
            .filter((p) => p !== undefined);
        const index = new_players.findIndex((p) => p.user_name === playerName);
        handleSetPlayers(new_players);
        handleSetPlayer(index);
        return state - 1;
    }
    return state;
}
