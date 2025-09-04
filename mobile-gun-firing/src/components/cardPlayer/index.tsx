import { View, Text, StyleSheet } from "react-native";

import { Player } from "@/src/dtos/players";
import { Image, useImage } from "expo-image";
type CardPlayerProps = {
    player: Player;
    playerMoment: number;
    index: number;
};

export default function CardPlayer({
    player,
    playerMoment,
    index,
}: CardPlayerProps) {
    const image = useImage(player.character?.avatar as string, {
        maxWidth: 400,
        onError(error) {
            console.error("Loading failed:", error.message);
        },
    });

    if (!image) {
        return <Text>Image is loading...</Text>;
    }

    return (
        <View
            style={[
                styles.parentItem,
                styles.borderedBox,
                {
                    backgroundColor:
                        player.identity === "Xerife" ? "#eecb02" : "white",
                    borderColor: playerMoment === index ? "green" : "white",
                },
            ]}
        >
            <View>
                {player.character?.avatar && (
                    <Image
                        style={styles.image}
                        source={image}
                        contentFit="cover"
                        transition={1000}
                    />
                )}
            </View>
            <View style={styles.player}>
                <View>
                    <Text style={styles.parentTitle}>
                        {player.user_name} - {player.identity}
                    </Text>
                    <Text style={styles.character}>
                        {player.character?.character} - {player.bullet}
                    </Text>
                </View>
                {playerMoment === index && (
                    <View style={[styles.borderedBox, styles.box]}>
                        <Text style={styles.boxIcon}>🎮</Text>
                    </View>
                )}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    parentItem: {
        padding: 10,
        borderBottomWidth: 1,
        borderBottomColor: "#ccc",
        flexDirection: "row",
        justifyContent: "space-between",
    },
    parentTitle: {
        fontSize: 18,
        fontWeight: "bold",
    },
    image: {
        height: 60,
        width: 60,
    },
    player: {
        width: "80%",
        flexDirection: "row",
        justifyContent: "space-between",
        paddingHorizontal: 15,
    },
    character: {
        fontSize: 14,
        fontWeight: "500",
    },
    borderedBox: {
        borderWidth: 2,
        borderRadius: 10,
        borderStyle: "dashed",
        backgroundColor: "lightgray",
    },
    box: {
        backgroundColor: "#3efa05ef",
        width: 48,
        height: 48,
        justifyContent: "center",
        alignItems: "center",
        borderRadius: 8,
    },
    boxIcon: {
        fontSize: 30,
    },
});
