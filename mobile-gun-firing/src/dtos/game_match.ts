export type GameStatus = "Done" | "Running" | "Cancelled" | "Idle";

export type BangDepartureType = {
    users: number[];
    status: GameStatus;
    player_of_the_moment: number;
};

export type CreateGameDTO = {
    player_name: string;
};

export type GameDTO = {
    _id: string;
    created_at: string;
    updated_at: string;
    updated_by: string;
    created_by: string;
    status: GameStatus;
    players_total: number;
    champion?: string;
    player_name: string;
};
