import React, { useEffect, useReducer, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import ChampionModal from "@/src/components/alerts/champion";
import { ButtonBase } from "@/src/components/buttonBase";
import DiceTray from "@/src/components/diceTray";
import EventToast from "@/src/components/eventToast";
import Table from "@/src/components/table";
import {
    TurnAction,
    TurnUi,
    canConfirm,
    canReroll,
    highlightedTargets,
    initialTurnUi,
    toAssignments,
    turnReducer,
    turnStage,
} from "@/src/game/turnReducer";
import { useGame } from "@/src/hooks/useGame";

export default function BangMatch() {
    const game = useGame("Lucas");
    const { view, animating, busy, error } = game;

    // O reducer recebe a visão atual do servidor a cada render
    const [ui, dispatch] = useReducer(
        (state: TurnUi, action: TurnAction) =>
            view ? turnReducer(state, action, view) : state,
        initialTurnUi,
    );
    const [championOpen, setChampionOpen] = useState(false);

    // Estado de interface vale para uma versão só: qualquer mudança do servidor zera
    const version = view?.version;
    useEffect(() => {
        dispatch({ type: "RESET" });
    }, [version]);

    const winner = view?.winner;
    useEffect(() => {
        setChampionOpen(Boolean(winner));
    }, [winner]);

    if (!view) {
        return (
            <View style={styles.loading}>
                <Text>{error ? `Erro: ${error}` : "Carregando partida..."}</Text>
                {error && <ButtonBase text="Tentar de novo" onPress={game.retry} />}
            </View>
        );
    }

    const stage = turnStage(view);
    // Durante a animação o estado mostrado ainda é o anterior: nada de ações
    const locked = busy || animating !== null;

    function handlePressDie(index: number) {
        if (stage === "ESCOLHENDO_REROLL") dispatch({ type: "TOGGLE_REROLL", index });
        if (stage === "ATRIBUINDO_DADOS") dispatch({ type: "SELECT_DIE", index });
    }

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <EventToast step={animating} onSkip={game.skipAnimation} />

            <Table
                view={view}
                animating={animating}
                highlightedIds={locked ? [] : highlightedTargets(ui, view)}
                assignments={ui.assignments}
                onPressPlayer={(player) =>
                    dispatch({ type: "ASSIGN", targetUserId: player.user_id })
                }
            />

            <DiceTray
                view={view}
                stage={stage}
                ui={ui}
                disabled={locked}
                onPressDie={handlePressDie}
            />

            <Text style={styles.hint}>{hintFor(stage, view.rolls_left)}</Text>
            {error && <Text style={styles.error}>{error}</Text>}

            <View style={styles.actions}>
                {stage === "PODE_ROLAR" && (
                    <ButtonBase text="Rolar dados" disabled={locked} onPress={() => game.roll([])} />
                )}
                {stage === "ESCOLHENDO_REROLL" && (
                    <>
                        <ButtonBase
                            text={`Rolar de novo (${ui.rerollMarked.length}) · restam ${view.rolls_left}`}
                            disabled={locked || !canReroll(ui, view)}
                            onPress={() => game.roll(ui.rerollMarked)}
                        />
                        <ButtonBase
                            text="Parar"
                            color="#6d4c41"
                            disabled={locked}
                            onPress={game.stopRolling}
                        />
                    </>
                )}
                {stage === "ATRIBUINDO_DADOS" && (
                    <ButtonBase
                        text="Confirmar"
                        disabled={locked || !canConfirm(ui, view)}
                        onPress={() => game.resolve(toAssignments(ui))}
                    />
                )}
                {stage === "ENCERRANDO" && (
                    <ButtonBase text="Encerrar turno" disabled={locked} onPress={game.finishTurn} />
                )}
                {error && !locked && (
                    <ButtonBase text="Tentar de novo" color="#c62828" onPress={game.retry} />
                )}
                {stage === "FIM" && (
                    <ButtonBase text="Nova partida" disabled={locked} onPress={game.newGame} />
                )}
            </View>

            {winner && (
                <ChampionModal
                    isVisible={championOpen}
                    onClose={() => setChampionOpen(false)}
                    teamChampion={winner}
                />
            )}
        </ScrollView>
    );
}

function hintFor(stage: ReturnType<typeof turnStage>, rollsLeft: number): string {
    switch (stage) {
        case "PODE_ROLAR":
            return "Sua vez: role os dados.";
        case "ESCOLHENDO_REROLL":
            return rollsLeft > 0
                ? "Toque nos dados que quer rolar de novo, ou pare."
                : "Sem rolagens restantes.";
        case "ATRIBUINDO_DADOS":
            return "Toque num dado destacado e depois num jogador aceso.";
        case "ENCERRANDO":
            return "Nada para atribuir: encerre o turno.";
        case "FIM":
            return "Fim de jogo.";
        default:
            return "Vez dos bots...";
    }
}

const styles = StyleSheet.create({
    loading: {
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
        gap: 12,
        padding: 16,
    },
    container: {
        paddingVertical: 8,
        gap: 8,
    },
    hint: {
        textAlign: "center",
        color: "#555",
        paddingHorizontal: 16,
    },
    error: {
        textAlign: "center",
        color: "#c62828",
        paddingHorizontal: 16,
    },
    actions: {
        paddingHorizontal: 16,
        gap: 8,
    },
});
