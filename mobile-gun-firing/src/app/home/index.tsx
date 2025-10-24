import { createGame } from "@/src/api/match_game";
import { useState } from "react";
import { View, Text, StyleSheet, Pressable } from "react-native";
import { useRouter } from "expo-router";
export default function Home() {
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();
    async function handleCreateGame() {
        try {
            setIsLoading(true);
            const data = await createGame({ player_name: "Lucas" });
            console.log(data?._id);
            router.push({
                pathname: `/bangMatch`,
                params: { game_id: data?._id },
            });
        } finally {
            setIsLoading(false);
        }
    }
    return (
        <View style={styles.container}>
            <View style={styles.card}>
                <Text style={styles.parentTitle}>Bem vindo ao bang</Text>
            </View>
            <View style={styles.card}>
                <View style={styles.card}>
                    <Pressable
                        onPress={handleCreateGame}
                        style={[styles.button]}
                        disabled={isLoading}
                    >
                        <Text style={styles.buttonText}>
                            Iniciar nova partida
                        </Text>
                    </Pressable>
                </View>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,

        // justifyContent: "center",
        padding: 10,
        // backgroundColor: "red",
    },
    footer: {
        flexDirection: "row",
        justifyContent: "space-between",
        padding: 10,
    },
    card: {
        // backgroundColor: "red",
    },
    parentItem: {
        padding: 10,
        borderBottomWidth: 1,
        borderBottomColor: "#ccc",
        flexDirection: "row",
        justifyContent: "space-between",
    },
    parentTitle: {
        fontSize: 20,
        fontWeight: "bold",
        // color: "red",
    },

    childItem: {
        fontSize: 16,
        marginLeft: 20,
    },
    button: {
        backgroundColor: "blue",
        borderRadius: 4,
        padding: 5,
    },
    buttonText: {
        color: "white",
        padding: 10,
        fontSize: 18,
    },
});
