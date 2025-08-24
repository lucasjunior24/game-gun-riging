import { characters, Identity } from "../consts/characters";
import { BangDeparture } from "../consts/game_match";
import { Player } from "../consts/players";

const identitys_list: Identity[] = [
  "Assistente",
  "Fora da lei",
  "Renegado",
  "Xerife",
];

export function create_players(): Player[] {
  const players = characters.map((c, i) => {
    const new_player: Player = {
      user_id: i + 1,
      is_alive: true,
      user_name: `User ${i + 1}`,
      character: c,
      identity: identitys_list[i],
      arrow: 0,
    };
    return new_player;
  });
  return players;
}

export function get_xerife(): Player {
  const players = create_players();
  const xerife = players.find((p) => p.identity === "Xerife");
  if (xerife) {
    return xerife;
  } else {
    throw new Error("O Xerife não foi criado");
  }
}
export function get_users_ids(): number[] {
  const players = create_players();
  const user_ids = players.map((p) => p.user_id);
  return user_ids;
}

export function get_player_of_the_moment(): string {
  const game = BangDeparture.getInstance();
  return game.get_player_of_the_moment();
}
export function pass_player(player_moment: string): string {
  console.log("player_moment", player_moment);
  const all_players = get_users_ids();
  if (all_players.length === Number(player_moment)) {
    return "1";
  }
  return `${Number(player_moment) + 1}`;
}
export function create_game(): BangDeparture {
  const game = BangDeparture.getInstance();
  return game;
}

export function get_player_by_user(user: number[], players: Player[]) {
  return players.filter((p) => {
    if (user.find((user) => user === p.user_id)) {
      return p;
    }
  });
}
