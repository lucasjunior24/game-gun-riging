import { get_users_ids, get_xerife } from "../game/init_game";

export type GameStatus = "Done" | "Running" | "Cancelled";

export type BangDepartureType = {
  users: number[];
  status: GameStatus;
  player_of_the_moment: number;
};

export class BangDeparture {
  users: number[];
  status: GameStatus;
  player_of_the_moment: number;
  private static instance: BangDeparture;
  // Constructor: A special method called when a new instance of the class is created

  constructor(
    users: number[],
    player_of_the_moment: number,
    status: GameStatus = "Running"
  ) {
    this.users = users; // 'this' refers to the current instance of the class
    this.player_of_the_moment = player_of_the_moment;
    this.status = status;
  }
  public static getInstance(): BangDeparture {
    if (!BangDeparture.instance) {
      const xerife = get_xerife();
      const user_ids = get_users_ids();
      BangDeparture.instance = new BangDeparture(user_ids, xerife.user_id);
    }
    return BangDeparture.instance;
  }
  // Method (behavior)
  get_player_of_the_moment(): string {
    return String(this.player_of_the_moment);
  }
}
