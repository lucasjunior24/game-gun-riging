import React, { useState } from "react";
import { Player } from "@/app/consts/players";
import { DiceCombinationUndefined, DiceOptions } from "@/app/consts/dice";
import { pass_player } from "@/app/game/init_game";
import { locked_dice, play_dice, sum_shoots } from "@/app/game/play_dice";
import { View, Text, StyleSheet, Pressable } from "react-native";
import Shoot from "../shoot";

interface RicesProps {
  players: Player[];
  playerMoment: string;
  handleSetPlayers(players: Player[]): void;
  setPlayerMoment: (user_id: string) => void;
}

function getEmogiDice(dice: DiceOptions | undefined) {
  switch (dice) {
    case "Dinamite":
      return "🧨";
    case "Cerveja":
      return "🍺";
    case "Flexa":
      return "🏹";
    case "Metralhadora":
      return "ᡕᠵ╤ᡁ᠊デ━";
    default:
      return dice;
  }
}
const Dices = ({
  handleSetPlayers,
  players,
  playerMoment,
  setPlayerMoment,
}: RicesProps) => {
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
  console.log("playerMoment", playerMoment);
  console.log();
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
  const player = players.filter((p) => p.user_id === Number(playerMoment))[0];
  const sumShoots = sum_shoots(diceOne, diceTwo, diceTree);
  return (
    <View style={styles.container}>
      <View style={styles.footer}>
        <View style={styles.card}>
          <Text style={styles.parentTitle}>Jogador atual</Text>
          <Text style={styles.parentTitle}>{player.user_name}</Text>
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
            <Pressable
              onPress={() => setDiceOne((state) => locked_dice(state))}
              style={[
                styles.buttonDice,
                {
                  backgroundColor: diceOne?.locked ? "red" : "blue",
                },
              ]}
            >
              <Text style={styles.text}> 🎲 </Text>
            </Pressable>
            <Text style={styles.icon}> {getEmogiDice(diceOne?.show)}</Text>
          </View>

          <View style={styles.dices}>
            <Pressable
              onPress={() => setDiceTwo((state) => locked_dice(state))}
              style={[
                styles.buttonDice,
                {
                  backgroundColor: diceTwo?.locked ? "red" : "blue",
                },
              ]}
            >
              <Text style={styles.text}> 🎲 </Text>
            </Pressable>
            <Text style={styles.icon}> {getEmogiDice(diceTwo?.show)}</Text>
          </View>

          <View style={styles.dices}>
            <Pressable
              onPress={() => setDiceTree((state) => locked_dice(state))}
              style={[
                styles.buttonDice,
                {
                  backgroundColor: diceTree?.locked ? "red" : "blue",
                },
              ]}
            >
              <Text style={styles.text}> 🎲 </Text>
            </Pressable>
            <Text style={styles.icon}> {getEmogiDice(diceTree?.show)}</Text>
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
export default Dices;

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
  icon: {
    fontSize: 24,
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
