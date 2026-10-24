import { Image } from "expo-image";
import { StyleSheet, Text, View } from "react-native";

import { characters } from "@/src/consts/characters";
import { Identity, PlayerView } from "@/src/dtos/gameView";

type PlayerSeatProps = {
    player: PlayerView;
    isMe: boolean;
    myIdentity?: Identity;
    isCurrent: boolean;
    highlighted: boolean;
    // Algo acontecendo com este jogador na animação (atirou, levou tiro...)
    active?: boolean;
    badges?: string[]; // dados já atribuídos a ele no turno do humano
};

function avatarOf(character: string): string | undefined {
    const name = character.trim();
    return characters.find((c) => c.character.trim() === name)?.avatar;
}

export default function PlayerSeat({
    player,
    isMe,
    myIdentity,
    isCurrent,
    highlighted,
    active = false,
    badges = [],
}: PlayerSeatProps) {
    const avatar = avatarOf(player.character);
    // O próprio papel é sempre visível para mim; dos outros, só o que o servidor revelou
    const identity = isMe ? myIdentity : player.public_identity;

    return (
        <View
            style={[
                styles.seat,
                isCurrent && styles.current,
                highlighted && styles.highlighted,
                active && styles.active,
                !player.is_alive && styles.dead,
            ]}
        >
            {avatar ? (
                <Image source={{ uri: avatar }} style={styles.avatar} contentFit="cover" />
            ) : (
                <View style={[styles.avatar, styles.placeholder]}>
                    <Text style={styles.placeholderText}>
                        {player.user_name.charAt(0).toUpperCase()}
                    </Text>
                </View>
            )}
            <Text style={styles.name} numberOfLines={1}>
                {isMe ? "Você" : player.user_name}
            </Text>
            {player.is_alive ? (
                <Text style={styles.stats}>
                    ❤️{player.life}/{player.max_life} 🏹{player.arrows}
                </Text>
            ) : (
                <Text style={styles.stats}>☠️ morto</Text>
            )}
            {identity && (
                <Text
                    style={[styles.identity, identity === "Xerife" && styles.sheriff]}
                    numberOfLines={1}
                >
                    {identity === "Xerife" ? "⭐ " : ""}
                    {identity}
                </Text>
            )}
            {badges.length > 0 && (
                <View style={styles.badges}>
                    {badges.map((badge, i) => (
                        <Text key={i} style={styles.badge}>
                            {badge}
                        </Text>
                    ))}
                </View>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    seat: {
        flex: 1,
        alignItems: "center",
        borderRadius: 10,
        borderWidth: 2,
        borderColor: "transparent",
        backgroundColor: "#fff",
        padding: 2,
    },
    current: {
        borderColor: "#2e7d32",
    },
    highlighted: {
        borderColor: "#f9a825",
        backgroundColor: "#fff59d",
    },
    active: {
        borderColor: "#c62828",
    },
    dead: {
        opacity: 0.45,
    },
    avatar: {
        width: 38,
        height: 38,
        borderRadius: 19,
    },
    placeholder: {
        backgroundColor: "#e0e0e0",
        justifyContent: "center",
        alignItems: "center",
    },
    placeholderText: {
        fontSize: 18,
        fontWeight: "bold",
        color: "#666",
    },
    name: {
        fontSize: 11,
        fontWeight: "bold",
    },
    stats: {
        fontSize: 10,
    },
    identity: {
        fontSize: 9,
        color: "#555",
    },
    sheriff: {
        color: "#b8860b",
        fontWeight: "bold",
    },
    badges: {
        position: "absolute",
        top: -8,
        right: -8,
        flexDirection: "row",
        gap: 2,
    },
    badge: {
        fontSize: 12,
        backgroundColor: "#1565c0",
        color: "#fff",
        borderRadius: 8,
        paddingHorizontal: 4,
        overflow: "hidden",
    },
});
