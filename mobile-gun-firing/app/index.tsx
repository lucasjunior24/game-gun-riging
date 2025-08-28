import React, { useEffect, useState } from "react";
import { View, FlatList, StyleSheet } from "react-native";

import { create_players } from "./game/init_game";
import Dices from "./components/dices";
import { Player } from "./consts/players";
import CardPlayer from "./components/cardPlayer";
import ChampionModal from "./components/alerts/champion";
import { Team } from "./consts/characters";
import { is_the_champion } from "./consts/champion";
// import CircularList from "./components/circularList";

const Index = () => {
  const data = create_players();

  const [players] = useState<Player[]>(data);
  const [livePlayers, setLivePlayers] = useState<Player[]>(players);

  function handleSetPlayers(players: Player[]) {
    setLivePlayers(players);
  }

  const [playerMoment, setPlayerMoment] = useState(players.length - 1);
  const [teamChampion, setTeamChampion] = useState<Team | undefined>(undefined);
  const [playerName, setPlayerName] = useState(
    players[players.length - 1].user_name
  );
  function handlePlayerMoment(user_id: number, user_name: string) {
    setPlayerMoment(user_id);
    setPlayerName(user_name);
  }

  const [openModal, setOpenModal] = useState(false);
  useEffect(() => {
    if (livePlayers.length) {
      setTeamChampion(is_the_champion(livePlayers));
    }
  }, [livePlayers]);

  useEffect(() => {
    if (teamChampion) {
      setOpenModal(true);
    }
  }, [teamChampion]);

  console.log(
    "team: ",
    players.map((p) => p.team),
    teamChampion
  );
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
      {teamChampion && (
        <ChampionModal
          isVisible={openModal}
          onClose={() => setOpenModal(!openModal)}
          teamChampion={teamChampion}
        />
      )}
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
