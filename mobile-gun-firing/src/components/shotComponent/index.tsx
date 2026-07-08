import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import {
    PropsWithChildren,
    useCallback,
    useEffect,
    useMemo,
    useState,
} from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";

import { ButtonBase } from "../buttonBase";

import { executeBotTurn, executeShots } from "@/src/api/game";
import { GameStateDTO } from "@/src/dtos/gameState";
import { sleep } from "@/src/utils/sleep";
import ListShots from "./listShots";

type ShootProps = PropsWithChildren<{
    isVisible: boolean;
    gameState: GameStateDTO;
    onClose: () => void;
    onStateUpdate: (newState: GameStateDTO) => void;
    onFinishPlayer: () => void;
}>;

export interface userBullets {
    user_name: string;
    shots: number;
}

export default function ShotComponent({
    isVisible,
    gameState,
    onClose,
    onStateUpdate,
    onFinishPlayer,
}: ShootProps) {
    const players = gameState.players;
    const currentPlayer = gameState.current_player;

    // Calcular alvos usando is_alive e user_id (não identidades!)
    const playersOneShot = useMemo(() => {
        return players.filter(
            (p) => p.is_alive && p.user_id !== currentPlayer.user_id,
        );
    }, [players, currentPlayer]);

    const playersTwoShot = useMemo(() => {
        // Distância 2 são os mesmos alvos que distância 1 para simplificar
        // Backend decide se há alvos válidos
        return players.filter(
            (p) => p.is_alive && p.user_id !== currentPlayer.user_id,
        );
    }, [players, currentPlayer]);

    // Contar tiros disponíveis com base nos dados
    const oneShotTotal = useMemo(() => {
        return gameState.dice.filter((d) => d.show === "1").length;
    }, [gameState.dice]);

    const twoShotTotal = useMemo(() => {
        return gameState.dice.filter((d) => d.show === "2").length;
    }, [gameState.dice]);

    const [userOneBullets, setUserOneBullets] = useState<userBullets[]>([]);
    const [userTwoBullets, setUserTwoBullets] = useState<userBullets[]>([]);

    // Executar tiros: envia comando ao backend, recebe novo estado
    const runExecution = useCallback(async () => {
        await sleep(4);

        const newState = await executeShots(gameState.game_id, {
            actor_user_id: currentPlayer.user_id,
            shots_by_distance: [
                {
                    distance: "1",
                    user_bullets: userOneBullets.map((u) => ({
                        user_name: u.user_name,
                        shots: u.shots,
                    })),
                },
                {
                    distance: "2",
                    user_bullets: userTwoBullets.map((u) => ({
                        user_name: u.user_name,
                        shots: u.shots,
                    })),
                },
            ],
        });
        if (newState) {
            onStateUpdate(newState);
            setUserOneBullets([]);
            setUserTwoBullets([]);
            onFinishPlayer();
        }
    }, [
        gameState.game_id,
        currentPlayer.user_id,
        userOneBullets,
        userTwoBullets,
        onStateUpdate,
        onFinishPlayer,
    ]);

    const runExecutionSleep = useCallback(async () => {
        await sleep(3);
        runExecution();
    }, [runExecution]);

    // Turno do bot: chama endpoint dedicado
    useEffect(() => {
        if (
            gameState.status === "Running" &&
            currentPlayer.is_bot &&
            isVisible &&
            userOneBullets.length === 0 &&
            userTwoBullets.length === 0
        ) {
            executeBotTurn(gameState.game_id).then((newState) => {
                if (newState) {
                    onStateUpdate(newState);
                    onFinishPlayer();
                }
            });
        }
        if (
            gameState.status === "Running" &&
            currentPlayer.is_bot &&
            isVisible &&
            (userOneBullets.length || userTwoBullets.length)
        ) {
            runExecutionSleep();
        }
    }, [
        currentPlayer.is_bot,
        currentPlayer.user_name,
        gameState.status,
        isVisible,
        userOneBullets.length,
        userTwoBullets.length,
        gameState.game_id,
        onStateUpdate,
        onFinishPlayer,
        runExecutionSleep,
    ]);

    return (
        <View>
            <Modal
                animationType="slide"
                transparent
                visible={isVisible}
                focusable
            >
                <View style={styles.modalContent}>
                    <View style={styles.titleContainer}>
                        <Text />
                        <Text style={styles.title}>Dar tiros</Text>
                        <Pressable onPress={onClose}>
                            <MaterialIcons
                                name="close"
                                color={"#000"}
                                size={26}
                            />
                        </Pressable>
                    </View>

                    <ListShots
                        distance={1}
                        bulletTotal={oneShotTotal}
                        playersOptions={playersOneShot}
                        setUser={setUserOneBullets}
                        userBullets={userOneBullets}
                    />
                    {twoShotTotal !== 0 && (
                        <ListShots
                            distance={players.length > 3 ? 2 : 1}
                            bulletTotal={twoShotTotal}
                            playersOptions={playersTwoShot}
                            setUser={setUserTwoBullets}
                            userBullets={userTwoBullets}
                        />
                    )}

                    <View style={{ padding: 10, paddingTop: 20 }}>
                        <ButtonBase onPress={runExecution} text="Executar" />
                    </View>
                </View>
            </Modal>
        </View>
    );
}

const styles = StyleSheet.create({
    modalContent: {
        width: "100%",

        borderTopRightRadius: 18,
        borderTopLeftRadius: 18,

        flexDirection: "column",

        justifyContent: "space-between",
        // padding: 10,
        backgroundColor: "#fff",
        position: "absolute",
        // height: 400,
        borderColor: "#000",
        borderStyle: "solid",
        borderWidth: StyleSheet.hairlineWidth,
        bottom: -10,
        borderRadius: 20,
        paddingBottom: 20,
    },
    titleContainer: {
        height: 60,
        width: "100%",
        borderTopRightRadius: 10,
        borderTopLeftRadius: 10,
        paddingHorizontal: 20,
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
    },
    title: {
        color: "blue",
        fontSize: 18,
        fontWeight: "bold",
    },
    parentItem: {
        padding: 10,
        borderBottomWidth: 1,
        borderBottomColor: "#ccc",
    },
    parentTitle: {
        fontSize: 18,
        fontWeight: "bold",
    },
});
