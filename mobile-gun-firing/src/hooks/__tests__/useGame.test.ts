import { act, renderHook, waitFor } from "@testing-library/react-native";

import * as gameApi from "../../api/game";
import { GameView } from "../../dtos/gameView";
import { gameView } from "../../test/fixtures";
import { resetSavedSession, useGame } from "../useGame";

jest.mock("../../api/game", () => ({
    ...jest.requireActual("../../api/game"),
    createGame: jest.fn(),
    getState: jest.fn(),
    roll: jest.fn(),
    advanceBots: jest.fn(),
}));

const api = jest.mocked(gameApi);

const created = {
    game_id: "g1",
    status: "Running" as const,
    round_number: 1,
    turn_number: 1,
    current_player_index: 0,
    players: [
        { user_id: 1, user_name: "Lucas", position: 0, is_alive: true, is_bot: false, arrow: 0, bullet: 8 },
        { user_id: 2, user_name: "Murilo", position: 1, is_alive: true, is_bot: true, arrow: 0, bullet: 8 },
    ],
};

const botTurn = gameView({ version: 1, current_user_id: 2, allowed_actions: ["WAIT_BOTS"] });
const humanTurn = gameView({ version: 2, allowed_actions: ["ROLL"], last_event_id: 7 });

function deferred<T>() {
    let resolve!: (value: T) => void;
    const promise = new Promise<T>((r) => (resolve = r));
    return { promise, resolve };
}

beforeEach(() => {
    jest.clearAllMocks();
    resetSavedSession();
    api.createGame.mockResolvedValue(created);
});

it("cria a partida com papéis sorteados e busca a visão do humano", async () => {
    api.getState.mockResolvedValue(humanTurn);
    const { result } = renderHook(() => useGame("Lucas"));

    await waitFor(() => expect(result.current.view).toEqual(humanTurn));
    expect(api.createGame).toHaveBeenCalledWith({
        player_name: "Lucas",
        players_total: 5,
        shuffle_roles: true,
    });
    expect(api.getState).toHaveBeenCalledWith("g1", 1);
});

it("duas chamadas seguidas a advanceBots geram uma requisição", async () => {
    api.getState.mockResolvedValue(botTurn);
    const pending = deferred<GameView>();
    api.advanceBots.mockReturnValue(pending.promise);

    const { result } = renderHook(() => useGame("Lucas"));
    await waitFor(() => expect(api.advanceBots).toHaveBeenCalledTimes(1));

    // O efeito já disparou uma; as duas próximas batem no inFlight
    act(() => {
        result.current.advanceBots();
        result.current.advanceBots();
    });
    expect(api.advanceBots).toHaveBeenCalledTimes(1);
    expect(api.advanceBots).toHaveBeenCalledWith("g1", { expected_version: 1, since_event_id: 0 });

    await act(async () => pending.resolve(humanTurn));
    await waitFor(() => expect(result.current.view).toEqual(humanTurn));
    expect(api.advanceBots).toHaveBeenCalledTimes(1);
});

it("um 409 leva a um getState", async () => {
    api.getState.mockResolvedValueOnce(humanTurn);
    const { result } = renderHook(() => useGame("Lucas"));
    await waitFor(() => expect(result.current.view).toEqual(humanTurn));

    const fresh = gameView({ version: 5, allowed_actions: ["ROLL", "STOP_ROLLING"], last_event_id: 9 });
    api.roll.mockRejectedValue({ isAxiosError: true, response: { status: 409 } });
    api.getState.mockResolvedValueOnce(fresh);

    await act(async () => {
        await result.current.roll([]);
    });

    expect(api.getState).toHaveBeenLastCalledWith("g1", 1, 7);
    expect(result.current.view).toEqual(fresh);
    expect(result.current.error).toBeNull();
    expect(result.current.busy).toBe(false);
});

it("um erro de rede não deixa o jogo travado", async () => {
    api.getState.mockResolvedValueOnce(humanTurn);
    const { result } = renderHook(() => useGame("Lucas"));
    await waitFor(() => expect(result.current.view).toEqual(humanTurn));

    api.roll.mockRejectedValueOnce(new Error("Network Error"));
    api.getState.mockResolvedValueOnce(humanTurn);
    await act(async () => {
        await result.current.roll([]);
    });
    expect(result.current.error).toBe("Network Error");

    // Destravado: a próxima ação chega à API
    api.roll.mockResolvedValueOnce({ ...humanTurn, version: 3 });
    await act(async () => {
        await result.current.roll([]);
    });
    expect(api.roll).toHaveBeenCalledTimes(2);
    expect(result.current.view?.version).toBe(3);
});
