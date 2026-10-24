import { DieView, GameEvent, GameView, PlayerView } from "../dtos/gameView";

export function player(overrides: Partial<PlayerView> = {}): PlayerView {
    const userId = overrides.user_id ?? 1;
    return {
        user_id: userId,
        user_name: `Jogador ${userId}`,
        seat: userId - 1,
        character: "",
        life: 8,
        max_life: 8,
        arrows: 0,
        is_alive: true,
        is_bot: userId !== 1,
        public_identity: null,
        distance_from_me: null,
        ...overrides,
    };
}

export function die(overrides: Partial<DieView> = {}): DieView {
    return {
        index: 0,
        face: null,
        locked: false,
        can_reroll: false,
        resolved: false,
        valid_target_user_ids: [],
        ...overrides,
    };
}

export function event(overrides: Partial<GameEvent> = {}): GameEvent {
    return {
        id: 1,
        type: "TIRO",
        round_number: 1,
        turn_number: 1,
        actor_user_id: null,
        target_user_id: null,
        amount: 0,
        actor_public_identity: null,
        target_public_identity: null,
        data: {},
        ...overrides,
    };
}

export function gameView(overrides: Partial<GameView> = {}): GameView {
    return {
        game_id: "g1",
        version: 1,
        status: "Running",
        phase: "ROLANDO",
        round_number: 1,
        turn_number: 1,
        current_user_id: 1,
        rolls_left: 3,
        arrows_in_pile: 9,
        me: { user_id: 1, identity: "Xerife" },
        players: [1, 2, 3, 4, 5].map((id) => player({ user_id: id })),
        dice: [0, 1, 2, 3, 4].map((index) => die({ index })),
        allowed_actions: ["ROLL"],
        winner: null,
        events: [],
        last_event_id: 0,
        ...overrides,
    };
}
