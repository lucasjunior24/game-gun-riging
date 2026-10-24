import { Pressable, StyleSheet, Text, View } from "react-native";

import { faceIcon } from "@/src/consts/diceFaces";
import { GameView } from "@/src/dtos/gameView";
import { TurnStage, TurnUi } from "@/src/game/turnReducer";

type DiceTrayProps = {
    view: GameView;
    stage: TurnStage;
    ui: TurnUi;
    disabled: boolean;
    onPressDie: (index: number) => void;
};

export default function DiceTray({ view, stage, ui, disabled, onPressDie }: DiceTrayProps) {
    // Na vez dos bots os dados mostram o turno deles, mas não respondem ao toque
    const mine = view.current_user_id === view.me.user_id;
    const names = new Map(view.players.map((p) => [p.user_id, p.user_name]));

    return (
        <View style={styles.tray}>
            {view.dice.map((die) => {
                const marked = ui.rerollMarked.includes(die.index);
                const selected = ui.selectedDie === die.index;
                const target = ui.assignments[die.index];
                const pending = !die.resolved && die.valid_target_user_ids.length > 0;
                const pressable =
                    mine &&
                    !disabled &&
                    ((stage === "ESCOLHENDO_REROLL" && die.can_reroll) ||
                        (stage === "ATRIBUINDO_DADOS" && pending));
                return (
                    <Pressable
                        key={die.index}
                        disabled={!pressable}
                        onPress={() => onPressDie(die.index)}
                        style={[
                            styles.die,
                            die.locked && styles.locked,
                            marked && styles.marked,
                            pending && styles.pending,
                            selected && styles.selected,
                            die.resolved && styles.resolved,
                        ]}
                    >
                        <Text style={styles.face}>{faceIcon(die.face)}</Text>
                        <Text style={styles.caption} numberOfLines={1}>
                            {die.locked
                                ? "travado"
                                : marked
                                  ? "rolar"
                                  : target !== undefined
                                    ? target === view.me.user_id
                                        ? "você"
                                        : names.get(target)
                                    : die.resolved
                                      ? "feito"
                                      : " "}
                        </Text>
                    </Pressable>
                );
            })}
        </View>
    );
}

const styles = StyleSheet.create({
    tray: {
        flexDirection: "row",
        justifyContent: "center",
        gap: 8,
        paddingVertical: 8,
    },
    die: {
        width: 56,
        height: 64,
        borderRadius: 10,
        borderWidth: 2,
        borderColor: "#bdbdbd",
        backgroundColor: "#fff",
        alignItems: "center",
        justifyContent: "center",
    },
    locked: {
        backgroundColor: "#ffcdd2",
        borderColor: "#c62828",
    },
    marked: {
        borderColor: "#1565c0",
        backgroundColor: "#bbdefb",
    },
    pending: {
        borderColor: "#f9a825",
    },
    selected: {
        borderWidth: 4,
        backgroundColor: "#fff59d",
    },
    resolved: {
        opacity: 0.4,
    },
    face: {
        fontSize: 26,
    },
    caption: {
        fontSize: 10,
        color: "#555",
        maxWidth: 52,
    },
});
