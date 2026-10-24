import { Pressable, StyleSheet, Text, View } from "react-native";

import { AnimationStep } from "@/src/game/eventQueue";

type EventToastProps = {
    step: AnimationStep | null;
    onSkip: () => void;
};

export default function EventToast({ step, onSkip }: EventToastProps) {
    if (!step) return <View style={styles.placeholder} />;
    return (
        <View style={styles.toast}>
            <Text style={styles.text} numberOfLines={2}>
                {step.text}
            </Text>
            <Pressable onPress={onSkip} style={styles.skip}>
                <Text style={styles.skipText}>Pular ⏭</Text>
            </Pressable>
        </View>
    );
}

const styles = StyleSheet.create({
    placeholder: {
        height: 48,
    },
    toast: {
        height: 48,
        marginHorizontal: 16,
        paddingHorizontal: 12,
        borderRadius: 10,
        backgroundColor: "#3e2723",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 8,
    },
    text: {
        flex: 1,
        color: "#fff",
        fontSize: 14,
        fontWeight: "500",
    },
    skip: {
        paddingVertical: 6,
        paddingHorizontal: 10,
        borderRadius: 6,
        backgroundColor: "#6d4c41",
    },
    skipText: {
        color: "#fff",
        fontSize: 12,
    },
});
