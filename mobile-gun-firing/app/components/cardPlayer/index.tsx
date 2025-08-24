import { View, Text, StyleSheet } from "react-native";

import { Player } from "@/app/consts/players";
import { Image, useImage } from "expo-image";
type CardPlayerProps = {
  player: Player;
};

export default function CardPlayer({ player }: CardPlayerProps) {
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
    <View style={styles.parentItem}>
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
        <Text style={styles.parentTitle}>
          {player.user_name} - {player.identity}
        </Text>
        <Text style={styles.character}>
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
  },
  character: {
    fontSize: 14,
    fontWeight: "500",
  },
});
