import { View, Text, StyleSheet } from "react-native";
import { PropsWithChildren } from "react";
import { Player } from "@/app/consts/players";

type ShootProps = PropsWithChildren<{
  player: Player;
}>;

export default function CardShoot({ player }: ShootProps) {
  return (
    <View style={styles.parentItem}>
      <View>
        <Text style={styles.parentTitle}>{player.user_name}</Text>
      </View>
      <View>
        <Text style={styles.parentTitle}>
          {player.character?.character} - {player.character?.bullet}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
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
