import { executeBotTurn, finishTurn, rollDice } from "@/src/api/game";
import {
    DiceShowDTO,
    GameStateDTO,
    RollDiceCommandDTO,
} from "@/src/dtos/gameState";
import { sleep } from "@/src/utils/sleep";
import React, { useCallback, useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Shot from "../shotComponent";
import DiceItem from "./diceItem";

interface DicesProps {
    gameState: GameStateDTO;
    onStateUpdate: (newState: GameStateDTO) => void;
}

const DicesComponent = ({ gameState, onStateUpdate }: DicesProps) => {
    const [lockedDiceIndexes, setLockedDiceIndexes] = useState<DiceShowDTO[]>(
        [],
    );
    const [openModal, setOpenModal] = useState(false);
    const [totalDiceRolls, setTotalDiceRolls] = useState(0);

    function clearDices() {
        setLockedDiceIndexes([]);
        setTotalDiceRolls(0);
    }

    const currentPlayer = gameState.current_player;

    // Retorna os índices dos dados que são Dinamite (valor 3)
    // console.log("lockedDiceIndexes: ", lockedDiceIndexes);
    console.log(
        "gameState.dice: ",
        currentPlayer.is_bot,
        currentPlayer.user_name,
    );
    const playAllDices = useCallback(async () => {
        const command: RollDiceCommandDTO = {
            locked_dice_indexes: lockedDiceIndexes,
        };

        const newState = await rollDice(gameState.game_id, command);
        await sleep(2);
        if (newState) {
            onStateUpdate(newState);
            setLockedDiceIndexes(
                newState.dice.sort((a, b) => a.index - b.index),
            );
        }
        setTotalDiceRolls((state) => state + 1);
    }, [gameState.game_id, lockedDiceIndexes, onStateUpdate]);

    function handleOpenModal() {
        setOpenModal(true);
    }

    function handleClose() {
        setOpenModal(false);
    }

    const finishPlayer = useCallback(() => {
        setOpenModal(false);
        clearDices();
    }, []);

    const runBotTurn = useCallback(
        async (game_id: string) => {
            const newState = await executeBotTurn(game_id);
            if (!newState) {
                console.error("Erro ao executar turno do bot");
                return;
            }
            await sleep(3);
            onStateUpdate(newState);
            finishPlayer();
        },
        [finishPlayer, onStateUpdate],
    );

    const toggleLockDice = (index: number) => {
        setLockedDiceIndexes((prev) => {
            const newLockedDice = gameState.dice.find((d) => d.index === index);
            if (newLockedDice === undefined) {
                return prev;
            }
            const dices = [
                ...prev.filter((d) => d.index !== index),
                {
                    dice: newLockedDice.dice,
                    locked: !newLockedDice.locked,
                    show: newLockedDice.show,
                    index: index,
                },
            ];
            return dices.sort((a, b) => a.index - b.index);
        });
    };

    // Turno do bot: executa rolagens e tiros automaticamente
    const botPlayAllDices = useCallback(async () => {
        await sleep(3);
        if (totalDiceRolls < 3) {
            await playAllDices();
        }
        if (totalDiceRolls === 2) {
            await sleep(3);
            setOpenModal(true);
        }
    }, [playAllDices, totalDiceRolls]);

    useEffect(() => {
        if (gameState.status === "Running" && currentPlayer.is_bot) {
            botPlayAllDices();
        }
    }, [botPlayAllDices, currentPlayer.is_bot, gameState.status]);

    // Bot turn: chama endpoint dedicado quando visível e é bot
    useEffect(() => {
        if (
            gameState.status === "Running" &&
            currentPlayer.is_bot &&
            openModal
        ) {
            runBotTurn(gameState.game_id);
        }
    }, [
        currentPlayer.is_bot,
        openModal,
        gameState.game_id,
        gameState.status,
        onStateUpdate,
        finishPlayer,
        runBotTurn,
    ]);

    return (
        <View style={styles.container}>
            <View style={styles.footer}>
                <View style={styles.card}>
                    <Text style={styles.parentTitle}>Jogador atual</Text>
                    <Text style={styles.parentTitle}>
                        {currentPlayer.user_name}
                    </Text>
                    <View style={styles.card}>
                        <Pressable
                            onPress={async () => {
                                const newState = await finishTurn(
                                    gameState.game_id,
                                );
                                if (newState) {
                                    onStateUpdate(newState);
                                    clearDices();
                                }
                            }}
                            style={styles.button}
                        >
                            <Text style={styles.text}>Passar Turno</Text>
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
                            <Text style={styles.text}>Rolar Dados</Text>
                        </Pressable>
                    </View>
                    <Text style={styles.parentTitle}>
                        Jogadas de dados {totalDiceRolls}
                    </Text>
                    <View style={styles.card}>
                        <Pressable
                            onPress={handleOpenModal}
                            style={[
                                styles.button,
                                { backgroundColor: "green" },
                            ]}
                        >
                            <Text style={styles.text}>Executar Tiros</Text>
                        </Pressable>
                    </View>
                </View>
                <View style={styles.card}>
                    <Text style={styles.parentTitle}>Dados</Text>
                    {lockedDiceIndexes.map((d, i) => (
                        <DiceItem
                            key={i}
                            dice={d}
                            handleDice={() => toggleLockDice(d.index)}
                        />
                    ))}
                </View>
            </View>
            <View>
                {gameState.status === "Running" && (
                    <Shot
                        isVisible={openModal}
                        onClose={handleClose}
                        gameState={gameState}
                        onStateUpdate={onStateUpdate}
                        onFinishPlayer={finishPlayer}
                    />
                )}
            </View>
        </View>
    );
};
export default DicesComponent;

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
