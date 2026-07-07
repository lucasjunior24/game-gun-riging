/**
 * @deprecated Este arquivo foi substituído por gameState.ts
 * GameStatus e CreateGameDTO agora estão em gameState.ts
 * GameDTO antigo foi substituído por GameStateDTO
 * Manter apenas para referência durante a migração
 */

export type GameStatus = "Done" | "Running" | "Cancelled" | "Idle";

export type BangDepartureType = {
    users: number[];
    status: GameStatus;
    player_of_the_moment: number;
};

/** @deprecated Usar CreateGameDTO de gameState.ts */
export type CreateGameDTO = {
    player_name: string;
};

/** @deprecated Usar GameStateDTO de gameState.ts */
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
