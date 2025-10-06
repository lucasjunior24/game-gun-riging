import { Modal, View, Text, Pressable, StyleSheet } from "react-native";
import {
    PropsWithChildren,
    useCallback,
    useEffect,
    useMemo,
    useState,
} from "react";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Player } from "@/src/dtos/players";
import { players_to_shot } from "@/src/game/shoot";

import { ButtonBase } from "../buttonBase";

import { DiceCombinationUndefined, ExecuteDicesDTO } from "@/src/dtos/dice";

import ListShots from "./listShots";
import { executeDices } from "@/src/api/dices";
import { sleep } from "@/src/utils/sleep";
import { useLocalSearchParams } from "expo-router";
// import { createPlayer } from "@/src/api/player";

function parsePlayers(new_players: Player[], user: userBullets) {
    new_players = new_players
        .map((p) => {
            if (p.user_name === user.user_name && p.bullet) {
                p.bullet -= user.shots;
                if (p.bullet < 1) {
                    return;
                }
                return p;
            }
            return p;
        })
        .filter((p) => p !== undefined);
    return new_players;
}
type ShootProps = PropsWithChildren<{
    isVisible: boolean;
    onClose: () => void;
    finishPlayer: () => void;
    playerMoment: number;
    playerName: string;
    players: Player[];
    currentPlayer: Player;
    shots: DiceCombinationUndefined[];
    handleSetPlayers(players: Player[]): void;
    handleSetPlayer(playerMoment: number, new_players: Player[]): void;
}>;

export interface userBullets {
    user_name: string;
    shots: number;
}

export default function Shot({
    isVisible,
    onClose,
    playerMoment,
    players,
    currentPlayer,
    shots,
    finishPlayer,
    playerName,
    handleSetPlayers,
    handleSetPlayer,
}: ShootProps) {
    const livePlayers = players;
    const { game_id } = useLocalSearchParams();
    const optionsOneShoot = players_to_shot(
        playerMoment + 1,
        livePlayers.length,
        1
    );

    const optionsTwoShoot = players_to_shot(
        playerMoment + 1,
        livePlayers.length,
        livePlayers.length === 2 ? 1 : 2
    );

    const playersOneShot = useMemo(() => {
        return optionsOneShoot
            .map((index) => livePlayers.find((user, i) => i === index))
            .filter((p) => p !== undefined)
            .filter((p) => p.user_name !== playerName);
    }, [livePlayers, optionsOneShoot, playerName]);

    // console.log(
    //   playersOneShot.map((p) => {
    //     return p.user_name;
    //   })
    // );

    const playersTwoShot = useMemo(() => {
        return optionsTwoShoot
            .map((index) => livePlayers.find((user, i) => i === index))
            .filter((p) => p !== undefined)
            .filter((p) => p.user_name !== playerName);
    }, [livePlayers, optionsTwoShoot, playerName]);

    const oneShotTotal = useMemo(() => {
        return shots.filter((s) => s?.show === "1").length;
    }, [shots]);

    const twoShotTotal = useMemo(() => {
        return shots.filter((s) => s?.show === "2").length;
    }, [shots]);

    const [userOneBullets, setUserOneBullets] = useState<userBullets[]>([]);
    const [userTwoBullets, setUserTwoBullets] = useState<userBullets[]>([]);

    const runExecution = useCallback(() => {
        let players_updated: Player[] = players;
        userOneBullets.forEach((user) => {
            players_updated = parsePlayers(players_updated, user);
        });

        userTwoBullets.forEach((user) => {
            players_updated = parsePlayers(players_updated, user);
        });

        handleSetPlayers(players_updated);
        const index = players_updated.findIndex(
            (p) => p.user_name === playerName
        );
        // console.log("index: ", index);
        handleSetPlayer(index, players_updated);
        setUserOneBullets([]);
        setUserTwoBullets([]);
        finishPlayer();
    }, [
        finishPlayer,
        handleSetPlayer,
        handleSetPlayers,
        playerName,
        players,
        userOneBullets,
        userTwoBullets,
    ]);
    const tableSituation = useMemo(() => {
        let table_situation = "";
        const total_players = `Atualmente o jogo tem ${players.length} Jogadores sendo eles: `;
        players.forEach((p) => {
            table_situation += `O jogador ${p.user_name} que tem ${p.bullet} vidas, `;
        });
        return total_players + table_situation;
    }, [players]);

    const botExecuteDices = useCallback(async () => {
        console.log("game_id: ", game_id);

        // console.log(tableSituation);
        console.log(typeof game_id);
        const executionDTO: ExecuteDicesDTO = {
            game_id: String(game_id),
            current_player: currentPlayer,
            table_situation: tableSituation,
            current_identity: String(currentPlayer.identity),
            one_distance: {
                bullet_total: oneShotTotal,
                players_options: playersOneShot,
                user_bullets: userOneBullets,
            },
            two_distance: undefined,
        };
        if (twoShotTotal !== 0) {
            executionDTO.two_distance = {
                bullet_total: twoShotTotal,
                players_options: playersTwoShot,
                user_bullets: userTwoBullets,
            };
        }

        // await createPlayer(currentPlayer);
        const data = await executeDices(executionDTO);
        if (data) {
            if (data.one_distance.user_bullets) {
                await sleep(2);
                setUserOneBullets(data.one_distance.user_bullets);
            }
            if (data.two_distance?.user_bullets) {
                await sleep(2);
                setUserTwoBullets(data.two_distance.user_bullets);
            }
        }
    }, [
        currentPlayer,
        game_id,
        oneShotTotal,
        playersOneShot,
        playersTwoShot,
        tableSituation,
        twoShotTotal,
        userOneBullets,
        userTwoBullets,
    ]);

    const runExecutionSleep = useCallback(async () => {
        await sleep(3);
        runExecution();
    }, [runExecution]);

    useEffect(() => {
        if (
            currentPlayer.is_bot &&
            isVisible &&
            userOneBullets.length === 0 &&
            userTwoBullets.length === 0
        ) {
            console.log(currentPlayer.user_name);
            botExecuteDices();
        }
        if (userOneBullets.length || userTwoBullets.length) {
            runExecutionSleep();
        }
    }, [
        botExecuteDices,
        currentPlayer.is_bot,
        currentPlayer.user_name,
        isVisible,
        runExecutionSleep,
        userOneBullets.length,
        userTwoBullets.length,
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
                            distance={livePlayers.length > 3 ? 2 : 1}
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
