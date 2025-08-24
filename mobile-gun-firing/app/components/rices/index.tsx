import React, { useState } from "react";
import { Player } from "@/app/consts/players";
import { DiceCombinationUndefined } from "@/app/consts/dice";
import { get_player_of_the_moment, pass_player } from "@/app/game/init_game";
import { locked_rice, play_dice, sum_shoots } from "@/app/game/play_dice";
import { View, Text, StyleSheet, Pressable } from "react-native";
import Shoot from "../shoot";

interface RicesProps {
  handleSetPlayers(players: Player[]): void;
  players: Player[];
}

const Rices = ({ handleSetPlayers, players }: RicesProps) => {
  const [playerMoment, setPlayerMoment] = useState(get_player_of_the_moment());
  const [diceOne, setDiceOne] = useState<DiceCombinationUndefined>();
  const [diceTwo, setDiceTwo] = useState<DiceCombinationUndefined>();
  const [diceTree, setDiceTree] = useState<DiceCombinationUndefined>();
  const [openModal, setOpenModal] = useState(false);
  const [totalDiceRolls, setTotalDiceRolls] = useState(0);
  function passPlayer() {
    setPlayerMoment(pass_player(playerMoment));
    setDiceOne(undefined);
    setDiceTwo(undefined);
    setDiceTree(undefined);
    setTotalDiceRolls(0);
  }
  function playAllRice() {
    if (diceOne?.locked !== true) {
      setDiceOne(play_dice());
    }
    if (diceTwo?.locked !== true) {
      setDiceTwo(play_dice());
    }
    if (diceTree?.locked !== true) {
      setDiceTree(play_dice());
    }
    setTotalDiceRolls((state) => {
      return (state += 1);
    });
  }

  function runMetralhadora() {
    const players_now = players.map((p) => {
      if (p.user_id === Number(playerMoment)) {
        return p;
      }
      if (p.character && p.character.bullet) {
        p.character.bullet -= 1;
      }
      return p;
    });
    handleSetPlayers(players_now);
  }
  function exeDices() {
    // runMetralhadora();
    setOpenModal(true);
  }
  const sumShoots = sum_shoots(diceOne, diceTwo, diceTree);
  return (
    <View style={styles.container}>
      <View style={styles.footer}>
        <View style={styles.card}>
          <Text style={styles.parentTitle}>Jogador atual: {playerMoment}</Text>
          <View style={styles.card}>
            <Pressable onPress={passPlayer} style={styles.button}>
              <Text style={styles.text}>Pass Player</Text>
            </Pressable>
          </View>
          <View style={styles.card}>
            <Pressable
              onPress={playAllRice}
              style={[
                styles.button,
                { backgroundColor: totalDiceRolls === 3 ? "red" : "blue" },
              ]}
              disabled={totalDiceRolls === 3}
            >
              <Text style={styles.text}>Play All Rice</Text>
            </Pressable>
          </View>
          <Text style={styles.parentTitle}>
            Jogadas de dados {totalDiceRolls}
          </Text>
          <View style={styles.card}>
            <Pressable
              onPress={exeDices}
              style={[styles.button, { backgroundColor: "green" }]}
            >
              <Text style={styles.text}>Execute Rices</Text>
            </Pressable>
          </View>
        </View>
        <View style={styles.card}>
          <Text style={styles.parentTitle}>Dados travados</Text>

          <View style={styles.dices}>
            <Text style={styles.parentTitle}> 🎲 </Text>
            <Pressable
              onPress={() => setDiceOne((state) => locked_rice(state))}
              style={[
                styles.buttonDice,
                {
                  backgroundColor: diceOne?.locked ? "red" : "blue",
                },
              ]}
            >
              <Text style={styles.text}>{diceOne?.locked ? "Sim" : "Não"}</Text>
            </Pressable>
            <Text style={styles.parentTitle}>{diceOne?.show}</Text>
          </View>

          <View style={styles.dices}>
            <Text style={styles.parentTitle}> 🎲 </Text>
            <Pressable
              onPress={() => setDiceTwo((state) => locked_rice(state))}
              style={[
                styles.buttonDice,
                {
                  backgroundColor: diceTwo?.locked ? "red" : "blue",
                },
              ]}
            >
              <Text style={styles.text}>{diceTwo?.locked ? "Sim" : "Não"}</Text>
            </Pressable>
            <Text style={styles.parentTitle}> {diceTwo?.show}</Text>
          </View>

          <View style={styles.dices}>
            <Text style={styles.parentTitle}> 🎲 </Text>
            <Pressable
              onPress={() => setDiceTree((state) => locked_rice(state))}
              style={[
                styles.buttonDice,
                {
                  backgroundColor: diceTree?.locked ? "red" : "blue",
                },
              ]}
            >
              <Text style={styles.text}>
                {diceTree?.locked ? "Sim" : "Não"}
              </Text>
            </Pressable>
            <Text style={styles.parentTitle}> {diceTree?.show}</Text>
          </View>
        </View>
      </View>
      <View>
        <Shoot
          isVisible={openModal}
          onClose={() => setOpenModal(!openModal)}
          playerMoment={playerMoment}
          players={players}
          shoots={sumShoots}
          handleSetPlayers={handleSetPlayers}
          passPlayer={passPlayer}
        />
      </View>
    </View>
  );
};
export default Rices;

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
    width: "50%",
  },
  dices: {
    flexDirection: "row",
    gap: 10,
    paddingBottom: 5,
  },
  buttonDice: {
    backgroundColor: "blue",
    borderRadius: 4,
    padding: 5,
    width: 40,
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
