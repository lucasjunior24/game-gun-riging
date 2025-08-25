import React, { useState } from "react";
import { View, FlatList, StyleSheet } from "react-native";

import {
  create_players,
  get_player_of_the_moment,
  pass_player,
} from "./game/init_game";
import Dices from "./components/dices";
import { Player } from "./consts/players";
import CardPlayer from "./components/cardPlayer";
import ChampionModal from "./components/alerts/champion";

const Index = () => {
  const data = create_players();

  const [Players] = useState<Player[]>(data);
  const [livePlayers, setLivePlayers] = useState<Player[]>(Players);

  function handleSetPlayers(players: Player[]) {
    setLivePlayers(players);
  }

  const [playerMoment, setPlayerMoment] = useState(get_player_of_the_moment());
  function handlePlayerMoment(user_id: string) {
    let user = user_id;
    let is_alive = false;

    while (is_alive === false) {
      console.log("new player moment: ", user);
      const player = livePlayers.filter((p) => p.user_id === Number(user))[0];
      if (player.is_alive) {
        setPlayerMoment(user);
        is_alive = true;
      } else {
        user = pass_player(user);
      }
    }
  }
  console.log("Moment: ", playerMoment);
  const [openModal, setOpenModal] = useState(false);

  return (
    <View style={styles.container}>
      <FlatList
        data={Players}
        renderItem={({ item }) => (
          <CardPlayer player={item} playerMoment={playerMoment} />
        )}
        keyExtractor={(item) => String(item.user_id)}
      />
      <Dices
        handleSetPlayers={handleSetPlayers}
        players={livePlayers}
        setPlayerMoment={handlePlayerMoment}
        playerMoment={playerMoment}
      />

      <ChampionModal
        isVisible={openModal}
        onClose={() => setOpenModal(!openModal)}
        playerMoment={playerMoment}
        players={livePlayers}
      />
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
