import { Link } from "expo-router";
import { View, Text, StyleSheet } from "react-native";

export function Home() {
    return (
        <View style={styles.container}>
            <View style={styles.card}>
                <Text style={styles.parentTitle}>Bem vindo ao bang</Text>
            </View>
            <View style={styles.card}>
                <Link style={styles.button} href={"/bangMatch"} asChild>
                    <Text style={styles.buttonText}>Iniciar nova partida</Text>
                </Link>
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
        // width: 150,
    },
    buttonText: {
        color: "white",
        padding: 10,
        fontSize: 18,
    },
});
