import { userBullets } from "../components/shot";
import { Player } from "./players";

export type Dice = 1 | 2 | 3 | 4 | 5 | 6;

export type DiceOptions =
    | "1"
    | "2"
    | "Cerveja"
    | "Dinamite"
    | "Metralhadora"
    | "Flexa";

export type DiceCombination = {
    dice: Dice;
    show: DiceOptions;
    locked: boolean;
};

export type DiceCombinationUndefined = DiceCombination | undefined;

export const DICES: DiceCombination[] = [
    { dice: 1, show: "1", locked: false },
    { dice: 2, show: "2", locked: false },
    { dice: 3, show: "Cerveja", locked: false },
    { dice: 4, show: "Dinamite", locked: false },
    { dice: 5, show: "Metralhadora", locked: false },
    { dice: 6, show: "Flexa", locked: false },
];

export type ExecuteDistanceDTO = {
    bullet_total: number;
    players_options: Player[];
    user_bullets: userBullets[];
};

export type ExecuteDicesDTO = {
    current_player: Player;
    current_identity: string;
    game_id: string;
    table_situation: string;
    one_distance: ExecuteDistanceDTO;
    two_distance?: ExecuteDistanceDTO;
};
