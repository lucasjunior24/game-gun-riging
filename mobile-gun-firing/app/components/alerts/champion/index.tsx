import { Modal, View, Text, Pressable, StyleSheet } from "react-native";
import { PropsWithChildren } from "react";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Player } from "@/app/consts/players";

import { ButtonBase } from "../../buttonBase";

type ShootProps = PropsWithChildren<{
  isVisible: boolean;
  onClose: () => void;
  playerMoment: string;
  players: Player[];
}>;

export default function ChampionModal({
  isVisible,
  onClose,
  playerMoment,
  players,
}: ShootProps) {
  return (
    <View>
      <Modal animationType="slide" transparent visible={isVisible} focusable>
        <View style={styles.modalContent}>
          <View style={styles.titleContainer}>
            <Text />
            <Text style={styles.title}>Parabens voce vencel</Text>
            <Pressable onPress={onClose}>
              <MaterialIcons name="close" color={"#000"} size={26} />
            </Pressable>
          </View>

          <View style={{ padding: 10, paddingTop: 20 }}>
            <ButtonBase onPress={onClose} text="Executar" />
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  modalContent: {
    width: "100%",

    borderTopRightRadius: 18,
    borderTopLeftRadius: 18,

    flexDirection: "column",

    justifyContent: "space-between",
    // padding: 10,
    backgroundColor: "#fff",
    position: "absolute",
    // height: 400,
    borderColor: "#000",
    borderStyle: "solid",
    borderWidth: StyleSheet.hairlineWidth,
    bottom: -10,
    borderRadius: 20,
    paddingBottom: 20,
  },
  titleContainer: {
    height: 60,
    width: "100%",
    borderTopRightRadius: 10,
    borderTopLeftRadius: 10,
    paddingHorizontal: 20,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: {
    color: "blue",
    fontSize: 18,
    fontWeight: "bold",
  },
  parentItem: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#ccc",
  },
  parentTitle: {
    fontSize: 18,
    fontWeight: "bold",
  },
});
