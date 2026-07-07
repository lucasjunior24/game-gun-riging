import { Image, useImage } from "expo-image";
import { StyleSheet, Text, View } from "react-native";

import { PublicPlayer } from "@/src/dtos/gameState";
import { Dispatch } from "react";
import { ButtonIcon } from "../buttonIcon";
import { userBullets } from "../shotComponent";

type ShootProps = {
    player: PublicPlayer;
    bulletTotal: number;
    userBullets: userBullets[];
    setUser: Dispatch<React.SetStateAction<userBullets[]>>;
};

export default function CardShoot({
    player,
    userBullets,
    bulletTotal,
    setUser,
}: ShootProps) {
    const avatarUrl = player.character?.avatar ?? "";
    const image = useImage(avatarUrl, {
        maxWidth: 800,
        onError(error) {
            console.error("Loading failed:", error.message);
        },
    });

    const user = userBullets.find((u) => u.user_name === player.user_name);
    const totalShot = userBullets.map((u) => u.shots);
    const sumTotalShot = totalShot.reduce(
        (accumulator, currentValue) => accumulator + currentValue,
        0,
    );

    return (
        <View
            style={[
                styles.parentItem,
                {
                    backgroundColor:
                        player.revealed_identity === "Xerife"
                            ? "yellow"
                            : "white",
                },
            ]}
        >
            <View>
                {avatarUrl && image ? (
                    <Image
                        style={styles.image}
                        source={image}
                        contentFit="cover"
                        transition={1000}
                    />
                ) : (
                    <View style={[styles.image, styles.placeholderImage]}>
                        <Text style={styles.placeholderText}>
                            {player.user_name.charAt(0).toUpperCase()}
                        </Text>
                    </View>
                )}
            </View>
            <View style={styles.player}>
                <View style={{ width: 180 }}>
                    <Text style={styles.parentTitle}>
                        {player.user_name}
                        {player.revealed_identity === "Xerife"
                            ? " - Xerife"
                            : ""}
                    </Text>
                    <Text style={styles.character}>
                        {player.character?.character ?? "Carregando..."} -{" "}
                        {player.bullet}
                    </Text>
                </View>
                <View
                    style={{
                        flexDirection: "row",
                        width: 90,
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >
                    <View style={{ width: 40 }}>
                        <ButtonIcon
                            disabled={bulletTotal === sumTotalShot}
                            onPress={() => {
                                setUser((state) => {
                                    const users = state.map((u) => {
                                        if (u.user_name === player.user_name) {
                                            u.shots += 1;
                                            return u;
                                        }
                                        return u;
                                    });
                                    if (users.length && user) {
                                        return users;
                                    }
                                    return [
                                        ...state,
                                        {
                                            user_name: player.user_name,
                                            shots: 1,
                                        },
                                    ];
                                });
                            }}
                            text={`${bulletTotal - sumTotalShot}`}
                        />
                    </View>
                    <View style={{ width: 40 }}>
                        {user && (
                            <ButtonIcon
                                disabled={user.shots === 0}
                                onPress={() => {
                                    setUser((state) => {
                                        const users = state.map((u) => {
                                            if (
                                                u.user_name === player.user_name
                                            ) {
                                                u.shots -= 1;
                                                return u;
                                            }
                                            return u;
                                        });
                                        return users;
                                    });
                                }}
                                text={`- ${user.shots}`}
                                color="red"
                            />
                        )}
                    </View>
                </View>
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
        backgroundColor: "#0553",
    },
    placeholderImage: {
        backgroundColor: "#e0e0e0",
        borderRadius: 8,
        justifyContent: "center",
        alignItems: "center",
    },
    placeholderText: {
        fontSize: 24,
        fontWeight: "bold",
        color: "#666",
    },
    player: {
        width: "100%",
        paddingLeft: 15,
        flexDirection: "row",
    },
    character: {
        fontSize: 14,
        fontWeight: "500",
    },
});
