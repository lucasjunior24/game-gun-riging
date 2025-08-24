import { View, Text, StyleSheet, FlatList } from "react-native";
import CardShoot from "../../cardShoot";
import { Player } from "@/app/consts/players";

interface ListShootsProps {
  shotTwoDistance: number;
  playersTwoShot: Player[];
  bulletTwo: number;
  handleTwoBullet: (player: Player) => void;
}

export default function ListShoots({
  shotTwoDistance,
  playersTwoShot,
  bulletTwo,
  handleTwoBullet,
}: ListShootsProps) {
  const VIEW = (
    <View>
      <View style={{ padding: 10 }}>
        <Text style={styles.title}>2 Distancia / {shotTwoDistance} Tiros</Text>
      </View>
      <View>
        <FlatList
          data={playersTwoShot}
          renderItem={({ item }) => (
            <CardShoot
              player={item}
              shoots={bulletTwo}
              handleBullet={handleTwoBullet}
            />
          )}
          keyExtractor={(item) => String(item.user_id)}
        />
      </View>
    </View>
  );
  return shotTwoDistance ? VIEW : <></>;
}

const styles = StyleSheet.create({
  title: {
    color: "blue",
    fontSize: 18,
    fontWeight: "bold",
  },
});
