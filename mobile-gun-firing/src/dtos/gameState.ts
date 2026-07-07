// Representa o jogador público - apenas o que a UI pode mostrar
export type PublicPlayer = {
    user_id: number;
    user_name: string;
    position: number;
    character?: Character;
    is_alive: boolean;
    is_bot: boolean;
    arrow: number;
    bullet: number;
    revealed_identity?: Identity; // SÓ o Xerife aparece aqui
};

// Tipos de Character e Identity (mantidos para referência)
export type Character = {
    initial_bullet: number;
    power: string;
    character: string;
    avatar: string;
};

export type Identity = "Xerife" | "Fora da lei" | "Renegado" | "Assistente";

export type Team = Exclude<Identity, "Assistente">;

// Dados mostrados em cada face de dado
export type DiceShowDTO = {
    dice: number;
    locked: boolean;
    show: string;
};

// Estado completo da partida vindo do backend
export type GameStateDTO = {
    game_id: string;
    status: "Running" | "Done";
    round_number: number;
    turn_number: number;
    current_player: PublicPlayer;
    current_player_index: number;
    players: PublicPlayer[];
    dice: DiceShowDTO[];
    available_actions: string[];
    winner?: Team;
};

// Comandos que o frontend envia ao backend
export type RollDiceCommandDTO = {
    locked_dice_indexes: number[];
};

export type ShootDistanceCommandDTO = {
    distance: string;
    user_bullets: UserBulletsDTO[];
};

export type ExecuteShotsCommandDTO = {
    actor_user_id: number;
    shots_by_distance: ShootDistanceCommandDTO[];
};

export type UserBulletsDTO = {
    user_name: string;
    shots: number;
};

export type CreateGameDTO = {
    player_name: string;
    players_total: number;
};
