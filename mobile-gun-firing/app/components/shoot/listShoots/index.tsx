import { View, Text, StyleSheet, FlatList } from "react-native";
import CardShoot from "../../cardShoot";
import { Player } from "@/app/consts/players";

interface ListShootsProps {
  distance: number;
  bulletTotal: number;
  playersTwoShot: Player[];
  bullet: number;
  handleTwoBullet: (player: Player) => void;
}

export default function ListShoots({
  distance,
  bulletTotal,
  playersTwoShot,
  bullet,
  handleTwoBullet,
}: ListShootsProps) {
  const VIEW = (
    <View>
      <View style={{ padding: 10 }}>
        <Text style={styles.title}>
          {distance} Distancia / {bullet} Tiros
        </Text>
      </View>
      <View>
        <FlatList
          data={playersTwoShot}
          renderItem={({ item }) => (
            <CardShoot
              player={item}
              shoots={bullet}
              handleBullet={handleTwoBullet}
            />
          )}
          keyExtractor={(item) => String(item.user_id)}
        />
      </View>
    </View>
  );
  return bulletTotal > 0 ? VIEW : <></>;
}

const styles = StyleSheet.create({
  title: {
    color: "blue",
    fontSize: 18,
    fontWeight: "bold",
  },
});
