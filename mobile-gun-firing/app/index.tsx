import React, { useState } from "react";
import { View, FlatList, StyleSheet } from "react-native";

import { create_players } from "./game/init_game";
import Rices from "./components/rices";
import { Player } from "./consts/players";
import CardPlayer from "./components/cardPlayer";

const Index = () => {
  const data = create_players();

  const [players, setPlayers] = useState<Player[]>(data);
  function handleSetPlayers(players: Player[]) {
    setPlayers(players);
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={players}
        renderItem={({ item }) => <CardPlayer player={item} />}
        keyExtractor={(item) => String(item.user_id)}
      />
      <Rices handleSetPlayers={handleSetPlayers} players={players} />
    </View>
  );
};
export default Index;

const styles = StyleSheet.create({
  container: {
    flexDirection: "column",
    justifyContent: "space-between",
  },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    padding: 10,
  },
  card: {
    paddingVertical: 15,
  },
  parentItem: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#ccc",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  parentTitle: {
    fontSize: 15,
    fontWeight: "bold",
  },

  childItem: {
    fontSize: 16,
    marginLeft: 20,
  },
  button: {
    backgroundColor: "blue",
    borderRadius: 4,
    padding: 5,
    width: 150,
  },
});
