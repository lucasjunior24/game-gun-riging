export type GameStatus = "Done" | "Running" | "Cancelled";

export type BangDepartureType = {
  users: number[];
  status: GameStatus;
  player_of_the_moment: number;
};
