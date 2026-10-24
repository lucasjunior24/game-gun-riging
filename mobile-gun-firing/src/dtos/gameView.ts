// Espelho do GameViewDTO, dos comandos e dos eventos da API autoritativa (Fase 2).
// O front so mostra o que vem aqui: nenhuma regra e calculada localmente.

export type Identity = "Xerife" | "Fora da lei" | "Renegado" | "Assistente";

export type Team = Exclude<Identity, "Assistente">;

export type GameStatus = "Running" | "Done";

export type TurnPhase = "ROLANDO" | "RESOLVENDO";

export type DiceFace =
    | "1"
    | "2"
    | "Dinamite"
    | "Cerveja"
    | "Flecha"
    | "Metralhadora";

export type AllowedAction =
    | "ROLL"
    | "STOP_ROLLING"
    | "RESOLVE"
    | "FINISH_TURN"
    | "WAIT_BOTS";

export type EventType =
    | "TURNO_INICIADO"
    | "DADO_ROLADO"
    | "FLECHA"
    | "ATAQUE_INDIGENA"
    | "DINAMITE"
    | "TIRO"
    | "CERVEJA"
    | "GATLING"
    | "DANO"
    | "MORTE"
    | "VITORIA";

export type MeView = {
    user_id: number;
    identity: Identity;
};

export type PlayerView = {
    user_id: number;
    user_name: string;
    seat: number;
    character: string;
    life: number;
    max_life: number;
    arrows: number;
    is_alive: boolean;
    is_bot: boolean;
    public_identity: Identity | null; // so Xerife ou morto
    distance_from_me: number | null;
};

export type DieView = {
    index: number;
    face: DiceFace | null;
    locked: boolean;
    can_reroll: boolean;
    resolved: boolean;
    valid_target_user_ids: number[];
};

export type GameEvent = {
    id: number;
    // string e nao EventType: o servidor pode mandar tipos que o front ainda nao conhece
    type: EventType | string;
    round_number: number;
    turn_number: number;
    actor_user_id: number | null;
    target_user_id: number | null;
    amount: number;
    actor_public_identity: Identity | null;
    target_public_identity: Identity | null;
    data: Record<string, unknown>;
};

export type GameView = {
    game_id: string;
    version: number;
    status: GameStatus;
    phase: TurnPhase;
    round_number: number;
    turn_number: number;
    current_user_id: number;
    rolls_left: number;
    arrows_in_pile: number;
    me: MeView;
    players: PlayerView[];
    dice: DieView[];
    allowed_actions: AllowedAction[];
    winner: Team | null;
    events: GameEvent[];
    last_event_id: number;
};

// ---------- comandos ----------

export type Command = {
    actor_user_id: number;
    expected_version: number;
};

export type RollCommand = Command & {
    reroll_indexes: number[];
};

export type Assignment = {
    dice_index: number;
    target_user_id: number;
};

export type ResolveCommand = Command & {
    assignments: Assignment[];
};

export type AdvanceBotsCommand = {
    expected_version: number;
    since_event_id?: number;
};
