import { ReactNode } from "react";
import { Pressable, StyleSheet, View, useWindowDimensions } from "react-native";

import { PlayerView } from "@/src/dtos/gameView";

export const SEAT_WIDTH = 74;
export const SEAT_HEIGHT = 96;

type CircularListProps = {
    players: PlayerView[];
    renderPlayer: (player: PlayerView, highlighted: boolean) => ReactNode;
    // Quem fica embaixo, no meio (normalmente "você")
    bottomUserId?: number;
    highlightedIds?: number[];
    onPressPlayer?: (player: PlayerView) => void;
    children?: ReactNode; // conteúdo do centro da mesa
};

export default function CircularList({
    players,
    renderPlayer,
    bottomUserId,
    highlightedIds = [],
    onPressPlayer,
    children,
}: CircularListProps) {
    const { width } = useWindowDimensions();
    const size = Math.min(width - 32, 420);
    const radius = size / 2 - Math.max(SEAT_WIDTH, SEAT_HEIGHT) / 2;
    const center = size / 2;

    const ordered = [...players].sort((a, b) => a.seat - b.seat);
    const start = Math.max(
        0,
        ordered.findIndex((p) => p.user_id === bottomUserId),
    );

    return (
        <View style={[styles.table, { width: size, height: size }]}>
            <View style={styles.center}>{children}</View>
            {ordered.map((player, i) => {
                // Ângulo 90° = embaixo. Os assentos seguem no sentido horário.
                const angle = Math.PI / 2 + ((i - start) * 2 * Math.PI) / ordered.length;
                const left = center + radius * Math.cos(angle) - SEAT_WIDTH / 2;
                const top = center + radius * Math.sin(angle) - SEAT_HEIGHT / 2;
                const highlighted = highlightedIds.includes(player.user_id);
                return (
                    <Pressable
                        key={player.user_id}
                        disabled={!highlighted || !onPressPlayer}
                        onPress={() => onPressPlayer?.(player)}
                        style={[styles.seat, { left, top }]}
                    >
                        {renderPlayer(player, highlighted)}
                    </Pressable>
                );
            })}
        </View>
    );
}

const styles = StyleSheet.create({
    table: {
        alignSelf: "center",
        borderRadius: 9999,
        borderWidth: 4,
        borderColor: "#8b5a2b",
        backgroundColor: "#f3e2c3",
    },
    center: {
        ...StyleSheet.absoluteFillObject,
        justifyContent: "center",
        alignItems: "center",
        padding: SEAT_HEIGHT,
    },
    seat: {
        position: "absolute",
        width: SEAT_WIDTH,
        height: SEAT_HEIGHT,
    },
});
