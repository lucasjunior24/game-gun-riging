import { Player } from "@/app/consts/players";
import { DiceCombination } from "@/app/consts/dice";
import { get_player_of_the_moment, pass_player } from "@/app/game/init_game";
import { play_dice } from "@/app/game/play_dice";
import React, { useState } from "react";
import { View, Text, StyleSheet, Pressable } from "react-native";

interface RicesProps {
  handleSetPlayers(players: Player[]): void;
  players: Player[];
}
const Rices = ({ handleSetPlayers, players }: RicesProps) => {
  const [playerMoment, setPlayerMoment] = useState(get_player_of_the_moment());
  const [diceOne, setDiceOne] = useState<DiceCombination | undefined>();
  const [diceTwo, setDiceTwo] = useState<DiceCombination | undefined>();
  const [diceTree, setDiceTree] = useState<DiceCombination | undefined>();
  const [totalDiceRolls, setTotalDiceRolls] = useState(0);
  function passPlayer() {
    setPlayerMoment(pass_player(playerMoment));
    setDiceOne(undefined);
    setDiceTwo(undefined);
    setDiceTree(undefined);
    setTotalDiceRolls(0);
  }
  function playAllRice() {
    if (diceOne?.show !== "Dinamite") {
      setDiceOne(play_dice());
    }
    if (diceTwo?.show !== "Dinamite") {
      setDiceTwo(play_dice());
    }
    if (diceTree?.show !== "Dinamite") {
      setDiceTree(play_dice());
    }
    setTotalDiceRolls((state) => {
      return (state += 1);
    });
  }

  function exeDices() {
    const players_now = players.map((p) => {
      if (p.character && p.character.bullet) {
        p.character.bullet -= 1;
      }
      return p;
    });
    handleSetPlayers(players_now);
  }
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
          <Text style={styles.parentTitle}>Jogar Dados</Text>

          <View style={styles.card}>
            <Text style={styles.parentTitle}>{diceOne?.show}</Text>
            <Pressable
              onPress={() => setDiceOne(play_dice())}
              style={styles.button}
            >
              <Text
                style={[
                  styles.text,
                  {
                    backgroundColor:
                      diceOne?.show === "Dinamite" ? "red" : "blue",
                  },
                ]}
              >
                Dado 1{" "}
              </Text>
            </Pressable>
          </View>

          <View style={styles.card}>
            <Text style={styles.parentTitle}>{diceTwo?.show}</Text>
            <Pressable
              onPress={() => setDiceTwo(play_dice())}
              style={styles.button}
            >
              <Text
                style={[
                  styles.text,
                  {
                    backgroundColor:
                      diceTwo?.show === "Dinamite" ? "red" : "blue",
                  },
                ]}
              >
                Dado 2
              </Text>
            </Pressable>
          </View>

          <View style={styles.card}>
            <Text style={styles.parentTitle}> {diceTree?.show}</Text>
            <Pressable
              onPress={() => setDiceTree(play_dice())}
              style={styles.button}
            >
              <Text
                style={[
                  styles.text,
                  {
                    backgroundColor:
                      diceTree?.show === "Dinamite" ? "red" : "blue",
                  },
                ]}
              >
                Dado 3
              </Text>
            </Pressable>
          </View>
        </View>
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
