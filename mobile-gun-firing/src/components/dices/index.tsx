import React, { useCallback, useEffect, useState } from "react";
import { Player } from "@/src/dtos/players";
import { DiceCombination, DiceCombinationUndefined } from "@/src/dtos/dice";
import { pass_player } from "@/src/game/init_game";
import { locked_dice, play_dice, sum_shots } from "@/src/game/play_dice";
import { View, Text, StyleSheet, Pressable } from "react-native";
import Shot from "../shot";
import DiceItem from "./diceItem";
import { sleep } from "@/src/utils/sleep";
import { validDices } from "@/src/api/dices";
import { GameStatus } from "@/src/dtos/game_match";

interface DicesProps {
    players: Player[];
    playerMoment: number;
    playerName: string;
    gameId: string;
    gameStatus: GameStatus;
    handleSetPlayers(players: Player[]): void;
    setPlayerMoment: (user_id: number, user_name: string) => void;
}

const Dices = ({
    players,
    playerMoment,
    playerName,
    gameId,
    gameStatus,
    handleSetPlayers,
    setPlayerMoment,
}: DicesProps) => {
    const [diceOne, setDiceOne] = useState<DiceCombinationUndefined>();
    const [diceTwo, setDiceTwo] = useState<DiceCombinationUndefined>();
    const [diceThree, setDiceThree] = useState<DiceCombinationUndefined>();
    const [diceFour, setDiceFour] = useState<DiceCombinationUndefined>();
    const [diceFive, setDiceFive] = useState<DiceCombinationUndefined>();

    const [openModal, setOpenModal] = useState(false);
    const [totalDiceRolls, setTotalDiceRolls] = useState(0);
    function clearDices() {
        setDiceOne(undefined);
        setDiceTwo(undefined);
        setDiceThree(undefined);
        setDiceFour(undefined);
        setDiceFive(undefined);
        setTotalDiceRolls(0);
    }
    const passPlayer = useCallback(() => {
        const new_pl = pass_player(playerMoment, players.length);
        const player = players[new_pl];

        setPlayerMoment(new_pl, player.user_name);
        clearDices();
    }, [playerMoment, players, setPlayerMoment]);

    function handleSetPlayer(playerMoment: number, new_players: Player[]) {
        const new_pl = pass_player(playerMoment, new_players.length);
        const player = new_players[new_pl];

        setPlayerMoment(new_pl, player.user_name);
        // setPlayerMoment(playerMoment, playerName);
    }
    const player = players.filter((p) => p.user_name === playerName)[0];
    console.log("playerMoment: ", playerMoment);
    const sumShots = sum_shots(diceOne, diceTwo, diceThree, diceFour, diceFive);
    const playAllDices = useCallback(async () => {
        if (
            diceOne?.locked !== true ||
            diceTwo?.locked !== true ||
            diceThree?.locked !== true ||
            diceFour?.locked !== true ||
            diceFive?.locked !== true
        ) {
            let dices: Map<string, DiceCombination> = new Map();
            dices.set("1", play_dice());
            dices.set("2", play_dice());
            dices.set("3", play_dice());
            dices.set("4", play_dice());
            dices.set("5", play_dice());

            console.log();

            const valuesArray = Array.from(dices.values());
            // console.log("dices: ", valuesArray);
            const result = await validDices(valuesArray);

            if (result) {
                if (diceOne?.locked !== true) {
                    setDiceOne(result[0]);
                }
                if (diceTwo?.locked !== true) {
                    setDiceTwo(result[1]);
                }
                if (diceThree?.locked !== true) {
                    setDiceThree(result[2]);
                }
                if (diceFour?.locked !== true) {
                    setDiceFour(result[3]);
                }
                if (diceFive?.locked !== true) {
                    setDiceFive(result[4]);
                }
            }
            dices.clear();
        }

        setTotalDiceRolls((state) => {
            return (state += 1);
        });
    }, [
        diceFive?.locked,
        diceFour?.locked,
        diceOne?.locked,
        diceThree?.locked,
        diceTwo?.locked,
    ]);

    // function runMetralhadora() {
    //   const players_now = players.map((p) => {
    //     if (p.user_id === Number(playerMoment)) {
    //       return p;
    //     }
    //     if (p.character && p.bullet) {
    //       p.bullet -= 1;
    //     }
    //     return p;
    //   });
    //   handleSetPlayers(players_now);
    // }
    function exeDices() {
        // runMetralhadora();
        setOpenModal(true);
    }
    function handleClose() {
        // runMetralhadora();

        setOpenModal(false);
    }

    function finishPlayer() {
        setOpenModal(false);
        clearDices();
    }

    const botPlayAllDices = useCallback(async () => {
        await sleep(3);
        if (player.is_bot && totalDiceRolls < 3) {
            // console.log("play All Dices: ", totalDiceRolls);
            await playAllDices();
        }
        if (player.is_bot && totalDiceRolls === 2) {
            await sleep(3);
            exeDices();
            // passPlayer();
        }
    }, [playAllDices, player.is_bot, totalDiceRolls]);

    useEffect(() => {
        if (gameStatus === "Running") {
            botPlayAllDices();
        }
    }, [botPlayAllDices, gameStatus]);

    // console.log("shots:  ", sumShoots);
    if (player === undefined) {
        return <Text>loading player...</Text>;
    }
    return (
        <View style={styles.container}>
            <View style={styles.footer}>
                <View style={styles.card}>
                    <Text style={styles.parentTitle}>Jogador atual</Text>
                    <Text style={styles.parentTitle}>{player.user_name}</Text>
                    <View style={styles.card}>
                        <Pressable onPress={passPlayer} style={styles.button}>
                            <Text style={styles.text}>Pass Player</Text>
                        </Pressable>
                    </View>
                    <View style={styles.card}>
                        <Pressable
                            onPress={playAllDices}
                            style={[
                                styles.button,
                                {
                                    backgroundColor:
                                        totalDiceRolls > 2 ? "red" : "blue",
                                },
                            ]}
                            disabled={totalDiceRolls > 2}
                        >
                            <Text style={styles.text}>Play All Dices</Text>
                        </Pressable>
                    </View>
                    <Text style={styles.parentTitle}>
                        Jogadas de dados {totalDiceRolls}
                    </Text>
                    <View style={styles.card}>
                        <Pressable
                            onPress={exeDices}
                            style={[
                                styles.button,
                                { backgroundColor: "green" },
                            ]}
                        >
                            <Text style={styles.text}>Execute Dices</Text>
                        </Pressable>
                    </View>
                </View>
                <View style={styles.card}>
                    <Text style={styles.parentTitle}>Dados travados</Text>
                    <DiceItem
                        dice={diceOne}
                        handleDice={() =>
                            setDiceOne((state) => locked_dice(state))
                        }
                    />
                    <DiceItem
                        dice={diceTwo}
                        handleDice={() =>
                            setDiceTwo((state) => locked_dice(state))
                        }
                    />
                    <DiceItem
                        dice={diceThree}
                        handleDice={() =>
                            setDiceThree((state) => locked_dice(state))
                        }
                    />
                    <DiceItem
                        dice={diceFour}
                        handleDice={() =>
                            setDiceFour((state) => locked_dice(state))
                        }
                    />
                    <DiceItem
                        dice={diceFive}
                        handleDice={() =>
                            setDiceFive((state) => locked_dice(state))
                        }
                    />
                </View>
            </View>
            <View>
                {gameStatus === "Running" && (
                    <Shot
                        isVisible={openModal}
                        onClose={handleClose}
                        finishPlayer={finishPlayer}
                        playerMoment={playerMoment}
                        players={players}
                        gameId={gameId}
                        currentPlayer={player}
                        shots={sumShots}
                        handleSetPlayers={handleSetPlayers}
                        playerName={playerName}
                        gameStatus={gameStatus}
                        handleSetPlayer={handleSetPlayer}
                    />
                )}
            </View>
        </View>
    );
};
export default Dices;

const styles = StyleSheet.create({
    container: {
        flexDirection: "column",
        justifyContent: "space-between",
    },
    footer: {
        flexDirection: "row",
        justifyContent: "space-between",
        padding: 10,
    },
    card: {
        paddingVertical: 15,
        width: "50%",
    },
    dices: {
        flexDirection: "row",
        gap: 10,
        paddingBottom: 5,
    },
    buttonDice: {
        backgroundColor: "blue",
        borderRadius: 4,
        padding: 5,
        width: 40,
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
    icon: {
        fontSize: 24,
        fontWeight: "bold",
    },
    childItem: {
        fontSize: 16,
        marginLeft: 20,
    },
    button: {
        backgroundColor: "blue",
        borderRadius: 4,
        padding: 5,
        width: 150,
    },
    text: {
        fontSize: 16,
        color: "#fff",
    },
});
