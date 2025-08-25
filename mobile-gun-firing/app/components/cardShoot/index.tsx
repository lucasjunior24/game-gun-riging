import { View, Text, StyleSheet } from "react-native";
import { Image, useImage } from "expo-image";

import { Player } from "@/app/consts/players";
import { ButtonIcon } from "../buttonIcon";

type ShootProps = {
  player: Player;
  shoots: number;
  handleBullet: (player: Player) => void;
};

export default function CardShoot({
  player,
  shoots,
  handleBullet,
}: ShootProps) {
  const image = useImage(player.character?.avatar as string, {
    maxWidth: 800,
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
        { backgroundColor: player.identity === "Xerife" ? "yellow" : "white" },
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
        <View style={{ width: 180 }}>
          <Text style={styles.parentTitle}>
            {player.user_name} - {player.identity}
          </Text>
          <Text style={styles.character}>
            {player.character?.character} - {player.bullet}
          </Text>
        </View>
        <View style={{ width: 40 }}>
          <ButtonIcon
            onPress={() => handleBullet(player)}
            text={` + ${shoots} `}
          />
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
