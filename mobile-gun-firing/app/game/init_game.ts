import { characters, Identity } from "../consts/characters";

import { Player } from "../consts/players";

const identitys_list: Identity[] = [
  "Assistente",
  "Fora da lei",
  "Fora da lei",
  "Renegado",
  "Xerife",
];

export function create_players(): Player[] {
  const users = ["Lucas", "Murilo", "Aragão", "Roberto", "Bot"];
  const players = characters.map((c, i) => {
    const new_player: Player = {
      user_id: i + 1,
      position: i + 1,
      is_alive: true,
      user_name: users[i],
      character: c,
      identity: identitys_list[i],
      arrow: 0,
      bullet: c.initial_bullet,
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
  const user_ids = players.map((p, index) => index);
  return user_ids;
}

export function get_player_of_the_moment(): string {
  const xerife = get_xerife();
  return String(xerife.user_id);
}
export function pass_player(
  player_moment: number,
  players_size: number
): number {
  let result = 0;
  if (players_size - 1 === player_moment) {
    result = 0;

    return result;
  }
  result = player_moment + 1;

  return result;
}

export function get_player_by_user(user: number[], players: Player[]) {
  return players.filter((p) => {
    if (user.find((user) => user === p.user_id)) {
      return p;
    }
  });
}
