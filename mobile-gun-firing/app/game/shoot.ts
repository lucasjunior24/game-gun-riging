export function shoot_to_the_right(
  player_moment: string,
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
  player_moment: string,
  size: number,
  distance: number
): number {
  if (size === Number(player_moment)) {
    return size - distance;
  } else if (Number(player_moment) < size) {
    const total = Number(player_moment) - distance;
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
  current_player: string,
  total_players: number,
  dice: number
) {
  const one_short_right = shoot_to_the_right(
    current_player,
    total_players,
    dice
  );
  const one_short_left = shoot_to_the_left(current_player, total_players, dice);
  const players = new Set([one_short_right, one_short_left]);
  const playersArray = Array.from(players);
  return playersArray;
}

const players_one = players_to_shot("4", 4, 1);
const players_two = players_to_shot("4", 4, 2);
console.log(players_one);
console.log(players_two);
