// Formato antigo, usado so pela resposta de POST /games (sai na Fase 6).
// Todo o resto da partida usa GameView (gameView.ts).
import { Identity, Team } from "./gameView";

export type { Identity, Team };

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

export type Character = {
    initial_bullet: number;
    power: string;
    character: string;
    avatar: string;
};

// Estado devolvido pela criação da partida
export type GameStateDTO = {
    game_id: string;
    status: "Running" | "Done";
    round_number: number;
    turn_number: number;
    current_player_index: number;
    players: PublicPlayer[];
    winner?: Team;
};

export type CreateGameDTO = {
    player_name: string;
    players_total: number;
    shuffle_roles: boolean;
};
