import { Character, Identity, Team } from "./characters";

export type Player = {
  user_name: string;
  position: number;
  user_id: number;
  character: Character | undefined;
  identity: Identity;
  is_alive: boolean;
  is_bot: boolean;
  arrow: number;
  bullet: number;
  team: Team;
};
