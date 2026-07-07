import { DiceShowDTO } from "@/src/dtos/gameState";

import { Pressable, View, Text, StyleSheet } from "react-native";

interface DiceItemProps {
    handleDice: () => void;
    dice: DiceShowDTO;
}
function getEmogiDice(show: string | undefined) {
    switch (show) {
        case "Dinamite":
            return "🧨";
        case "Cerveja":
            return "🍺";
        case "Flexa":
            return "🏹";
        case "Metralhadora":
            return "ᡕᠵ╤ᡁ᠊デ━";
        default:
            return show;
    }
}
export default function DiceItem({ dice, handleDice }: DiceItemProps) {
    return (
        <View style={styles.dices}>
            <Pressable
                onPress={handleDice}
                style={[
                    styles.buttonDice,
                    {
                        backgroundColor: dice?.locked ? "red" : "blue",
                    },
                ]}
            >
                <Text style={styles.text}> 🎲 </Text>
            </Pressable>
            <Text style={styles.icon}> {getEmogiDice(dice?.show)}</Text>
        </View>
    );
}

const styles = StyleSheet.create({
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
    icon: {
        fontSize: 24,
        fontWeight: "bold",
    },

    text: {
        fontSize: 16,
        color: "#fff",
    },
});
