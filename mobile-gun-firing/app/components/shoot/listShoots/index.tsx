import { View, Text, StyleSheet, FlatList } from "react-native";
import CardShoot from "../../cardShoot";
import { Player } from "@/app/consts/players";
import { userBullets } from "..";
import { Dispatch } from "react";

interface ListShootsProps {
  distance: number;
  bulletTotal: number;
  playersOptions: Player[];
  bullet: number;
  userBullets: userBullets[];
  setUser: Dispatch<React.SetStateAction<userBullets[]>>;
}

export default function ListShoots({
  distance,
  bulletTotal,
  playersOptions,
  bullet,
  userBullets,
  setUser,
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
          data={playersOptions}
          renderItem={({ item }) => (
            <CardShoot
              player={item}
              shoots={bullet}
              setUser={setUser}
              userBullets={userBullets}
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
