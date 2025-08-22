import { Character, Identity } from "./characters";

export type Player = {
    user_name: string;
    user_id: number;
    character: Character | undefined;
    identity: Identity;
    is_alive: boolean;
};
