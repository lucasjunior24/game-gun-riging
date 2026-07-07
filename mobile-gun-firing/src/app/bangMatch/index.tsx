import ChampionModal from "@/src/components/alerts/champion";
import CardPlayer from "@/src/components/cardPlayer";
import Dices from "@/src/components/dices";
import { GameStateDTO } from "@/src/dtos/gameState";
import React, { useCallback, useEffect, useState } from "react";
import { FlatList, StyleSheet, View } from "react-native";

import { createGame } from "@/src/api/game";

export default function BangMatch() {
    const [gameState, setGameState] = useState<GameStateDTO | null>(null);
    const [gameID, setGameID] = useState<string | null>(null);
    const [openModal, setOpenModal] = useState(false);

    console.log("game_id", gameID);
    console.log("gameState", gameState);
    // Criar partida via POST /games usando a nova API

    async function initializeGame() {
        try {
            const state = await createGame({
                player_name: "Lucas",
                players_total: 5,
            });
            console.log("state", state);
            if (state) {
                setGameState(state);
                setGameID(state.game_id);
            }
        } catch (error) {
            console.error("Erro ao criar partida:", error);
        }
    }
    const initializeGameRun = useCallback(() => {
        initializeGame();
    }, []);
    useEffect(() => {
        initializeGameRun();
    }, [initializeGameRun]);

    // Atualizar estado a cada ação
    const handleStateUpdate = (newState: GameStateDTO) => {
        setGameState(newState);
    };

    // Verificar se o jogo acabou
    useEffect(() => {
        if (gameState?.status === "Done" && gameState?.winner) {
            setOpenModal(true);
        }
    }, [gameState?.status, gameState?.winner]);

    if (!gameState) {
        return (
            <View style={styles.container}>
                <CardPlayer
                    player={{
                        user_id: 0,
                        user_name: "Carregando...",
                        position: 0,
                        is_alive: true,
                        is_bot: false,
                        arrow: 0,
                        bullet: 0,
                    }}
                    playerMoment={-1}
                    index={-1}
                />
            </View>
        );
    }

    const { status, players, current_player_index, winner } = gameState;

    return (
        <View style={styles.container}>
            <FlatList
                data={players}
                renderItem={({ index, item }) => (
                    <CardPlayer
                        player={item}
                        playerMoment={current_player_index}
                        index={index}
                    />
                )}
                keyExtractor={(item, index) => String(index)}
            />
            <Dices gameState={gameState} onStateUpdate={handleStateUpdate} />
            {status === "Done" && winner && (
                <ChampionModal
                    isVisible={openModal}
                    onClose={() => setOpenModal(!openModal)}
                    teamChampion={winner}
                />
            )}
        </View>
    );
}

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
    },
    parentItem: {
        padding: 10,
        borderBottomWidth: 1,
        borderBottomColor: "#ccc",
        flexDirection: "row",
        justifyContent: "space-between",
    },
    parentTitle: {
        fontSize: 15,
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
});
