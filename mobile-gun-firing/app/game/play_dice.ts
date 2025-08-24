import {
  DiceCombination,
  DiceCombinationUndefined,
  DICES,
} from "../consts/dice";

function get_random_dice(): number {
  const min = 1;
  const max = 6;

  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function play_dice(): DiceCombination {
  const new_dice = get_random_dice();
  const data = DICES.filter((r) => r.dice === new_dice)[0];
  const dice = block_dinamite(data);
  return dice;
}

export function block_dinamite(dice: DiceCombination) {
  if (dice.show === "Dinamite") {
    dice.locked = true;
    return dice;
  }
  return dice;
}

export function locked_dice(
  state: DiceCombinationUndefined
): DiceCombinationUndefined {
  if (state) {
    return { ...state, locked: !state.locked };
  }
  return state;
}

export function sum_shoots(
  diceOne: DiceCombinationUndefined,
  diceTwo: DiceCombinationUndefined,
  diceTree: DiceCombinationUndefined
): DiceCombinationUndefined[] {
  const dices: DiceCombinationUndefined[] = [];
  if (diceOne?.show === "1" || diceOne?.show === "2") {
    dices.push(diceOne);
  }
  if (diceTwo?.show === "1" || diceTwo?.show === "2") {
    dices.push(diceTwo);
  }
  if (diceTree?.show === "1" || diceTree?.show === "2") {
    dices.push(diceTree);
  }
  return dices;
}
