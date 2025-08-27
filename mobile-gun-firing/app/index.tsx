import React, { useEffect, useState } from "react";
import { View, FlatList, StyleSheet } from "react-native";

import { create_players } from "./game/init_game";
import Dices from "./components/dices";
import { Player } from "./consts/players";
import CardPlayer from "./components/cardPlayer";
import ChampionModal from "./components/alerts/champion";
// import CircularList from "./components/circularList";

const Index = () => {
  const data = create_players();

  const [Players] = useState<Player[]>(data);
  const [livePlayers, setLivePlayers] = useState<Player[]>(Players);

  function handleSetPlayers(players: Player[]) {
    setLivePlayers(players);
  }

  const [playerMoment, setPlayerMoment] = useState(3);
  const [playerName, setPlayerName] = useState(Players[3].user_name);
  function handlePlayerMoment(user_id: number, user_name: string) {
    setPlayerMoment(user_id);
    setPlayerName(user_name);
  }

  const [openModal, setOpenModal] = useState(false);

  useEffect(() => {
    if (livePlayers.length === 1) {
      setOpenModal(true);
    }
  }, [livePlayers.length]);
  return (
    <View style={styles.container}>
      <FlatList
        data={livePlayers}
        renderItem={({ index, item }) => (
          <CardPlayer player={item} playerMoment={playerMoment} index={index} />
        )}
        keyExtractor={(item, index) => String(index)}
      />
      {/* <CircularList /> */}
      <Dices
        handleSetPlayers={handleSetPlayers}
        players={livePlayers}
        setPlayerMoment={handlePlayerMoment}
        playerMoment={playerMoment}
        playerName={playerName}
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
