import { Modal, View, Text, Pressable, StyleSheet } from "react-native";
import { PropsWithChildren, useEffect, useMemo, useState } from "react";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Player } from "@/src/dtos/players";
import { players_to_shot } from "@/src/game/shoot";

import { ButtonBase } from "../buttonBase";

import { DiceCombinationUndefined } from "@/src/dtos/dice";

import ListShoots from "./listShoots";
function parsePlayers(new_players: Player[], user: userBullets) {
    new_players = new_players
        .map((p) => {
            if (p.user_name === user.index && p.bullet) {
                p.bullet -= user.shoots;
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
    shoots: DiceCombinationUndefined[];
    handleSetPlayers(players: Player[]): void;
    handleSetPlayer(playerMoment: number, new_players: Player[]): void;
}>;

export interface userBullets {
    index: string;
    shoots: number;
}

export default function Shoot({
    isVisible,
    onClose,
    playerMoment,
    players,
    shoots,
    finishPlayer,
    playerName,
    handleSetPlayers,
    handleSetPlayer,
}: ShootProps) {
    const livePlayers = players;

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
        return shoots.filter((s) => s?.show === "1").length;
    }, [shoots]);

    const twoShotTotal = useMemo(() => {
        return shoots.filter((s) => s?.show === "2").length;
    }, [shoots]);

    const [userOneBullets, setUserOneBullets] = useState<userBullets[]>([]);
    const [userTwoBullets, setUserTwoBullets] = useState<userBullets[]>([]);

    function execution() {
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
    }

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

                    <ListShoots
                        distance={1}
                        bulletTotal={oneShotTotal}
                        playersOptions={playersOneShot}
                        setUser={setUserOneBullets}
                        userBullets={userOneBullets}
                    />
                    {twoShotTotal !== 0 && (
                        <ListShoots
                            distance={livePlayers.length > 3 ? 2 : 1}
                            bulletTotal={twoShotTotal}
                            playersOptions={playersTwoShot}
                            setUser={setUserTwoBullets}
                            userBullets={userTwoBullets}
                        />
                    )}

                    <View style={{ padding: 10, paddingTop: 20 }}>
                        <ButtonBase onPress={execution} text="Executar" />
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
