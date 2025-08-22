import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";

import { create_players, get_player_of_the_moment } from "./game/init_game";

const Index = () => {
  const data = create_players();
  const player_of_the_moment = get_player_of_the_moment();
  console.log(player_of_the_moment);

  return (
    <View style={styles.container}>
      <FlatList
        data={data}
        renderItem={({ item }) => (
          <View style={styles.parentItem}>
            <Text style={styles.parentTitle}>{item.user_name}</Text>
            <Text style={styles.parentTitle}>{item.identity}</Text>
            <Text style={styles.parentTitle}>{item.character?.character}</Text>
          </View>
        )}
        keyExtractor={(item) => String(item.user_id)}
      />
      <View>
        <Text style={styles.parentTitle}>
          Jogador atual: {player_of_the_moment}
        </Text>
      </View>
    </View>
  );
};
export default Index;

const styles = StyleSheet.create({
  container: {
    flexDirection: "column",
    justifyContent: "space-between",
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
  childItem: {
    fontSize: 16,
    marginLeft: 20,
  },
});
