import { RiceCombination, RICES } from "../consts/rice";

function get_random_dice(): number {
  const min = 1;
  const max = 6;

  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function play_dice(): RiceCombination {
  const rice = get_random_dice();
  const data = RICES.filter((r) => r.rice === rice)[0];
  return data;
}

export function block_dinamite(rice: RiceCombination) {
  if (rice.show === "Dinamite") {
    return rice;
  }
}
