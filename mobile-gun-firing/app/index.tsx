import React from "react";
import { View, Text, FlatList, StyleSheet } from "react-native";

import { create_players } from "./game/init_game";

import Rices from "./components/rices";

const Index = () => {
  const data = create_players();

  return (
    <View style={styles.container}>
      <FlatList
        data={data}
        renderItem={({ item }) => (
          <View style={styles.parentItem}>
            <View>
              <Text style={styles.parentTitle}>{item.user_name}</Text>
              <Text style={styles.parentTitle}>{item.identity}</Text>
            </View>
            <View>
              <Text style={styles.parentTitle}>
                {item.character?.character}
              </Text>
              <Text style={styles.parentTitle}>{item.character?.bullet}</Text>
            </View>
          </View>
        )}
        keyExtractor={(item) => String(item.user_id)}
      />
      <Rices />
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
    fontSize: 18,
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
  text: {
    fontSize: 16,
    color: "#fff",
  },
});
