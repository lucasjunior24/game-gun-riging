import { StyleSheet, Text, View } from "react-native";

import { faceIcon } from "@/src/consts/diceFaces";
import { GameView, PlayerView } from "@/src/dtos/gameView";
import { AnimationStep } from "@/src/game/eventQueue";
import CircularList from "../circularList";
import PlayerSeat from "../playerSeat";

type TableProps = {
    view: GameView;
    animating: AnimationStep | null;
    highlightedIds: number[];
    assignments: Record<number, number>; // dice_index -> target_user_id
    onPressPlayer: (player: PlayerView) => void;
};

export default function Table({
    view,
    animating,
    highlightedIds,
    assignments,
    onPressPlayer,
}: TableProps) {
    // Selos dos dados já atribuídos, por jogador
    const badges = new Map<number, string[]>();
    for (const [index, target] of Object.entries(assignments)) {
        const face = view.dice[Number(index)]?.face;
        badges.set(target, [...(badges.get(target) ?? []), faceIcon(face)]);
    }

    const activeIds = animating
        ? [animating.event.actor_user_id, animating.event.target_user_id]
        : [];

    return (
        <CircularList
            players={view.players}
            bottomUserId={view.me.user_id}
            highlightedIds={highlightedIds}
            onPressPlayer={onPressPlayer}
            renderPlayer={(player, highlighted) => (
                <PlayerSeat
                    player={player}
                    isMe={player.user_id === view.me.user_id}
                    myIdentity={view.me.identity}
                    isCurrent={player.user_id === view.current_user_id}
                    highlighted={highlighted}
                    active={activeIds.includes(player.user_id)}
                    badges={badges.get(player.user_id)}
                />
            )}
        >
            <View style={styles.info}>
                <Text style={styles.infoText}>Rodada {view.round_number}</Text>
                <Text style={styles.infoText}>🏹 na pilha: {view.arrows_in_pile}</Text>
                <Text style={styles.role}>Seu papel: {view.me.identity}</Text>
            </View>
        </CircularList>
    );
}

const styles = StyleSheet.create({
    info: {
        alignItems: "center",
        gap: 2,
    },
    infoText: {
        fontSize: 12,
        color: "#4e342e",
    },
    role: {
        fontSize: 13,
        fontWeight: "bold",
        color: "#4e342e",
        textAlign: "center",
    },
});
