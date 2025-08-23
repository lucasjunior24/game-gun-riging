import { RiceCombination } from "@/app/consts/rice";
import { get_player_of_the_moment, pass_player } from "@/app/game/init_game";
import { play_dice } from "@/app/game/play_dice";
import React, { useState } from "react";
import { View, Text, StyleSheet, Pressable } from "react-native";

const Rices = () => {
  const [playerMoment, setPlayerMoment] = useState(get_player_of_the_moment());
  const [riceOne, setRiceOne] = useState<RiceCombination | undefined>();
  const [riceTwo, setRiceTwo] = useState<RiceCombination | undefined>();
  const [riceTree, setRiceTree] = useState<RiceCombination | undefined>();
  const [totalDiceRolls, setTotalDiceRolls] = useState(0);
  function passPlayer() {
    setPlayerMoment(pass_player(playerMoment));
    setRiceOne(undefined);
    setRiceTwo(undefined);
    setRiceTree(undefined);
    setTotalDiceRolls(0);
  }
  function playAllRice() {
    console.log("play all rices");
    if (riceOne?.show !== "Dinamite") {
      setRiceOne(play_dice());
    }
    if (riceTwo?.show !== "Dinamite") {
      setRiceTwo(play_dice());
    }
    if (riceTree?.show !== "Dinamite") {
      setRiceTree(play_dice());
    }
    setTotalDiceRolls((state) => {
      return (state += 1);
    });
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
        </View>
        <View style={styles.card}>
          <Text style={styles.parentTitle}>Jogar Dados</Text>

          <View style={styles.card}>
            <Text style={styles.parentTitle}>{riceOne?.show}</Text>
            <Pressable
              onPress={() => setRiceOne(play_dice())}
              style={styles.button}
            >
              <Text
                style={[
                  styles.text,
                  {
                    backgroundColor:
                      riceOne?.show === "Dinamite" ? "red" : "blue",
                  },
                ]}
              >
                Dado 1{" "}
              </Text>
            </Pressable>
          </View>

          <View style={styles.card}>
            <Text style={styles.parentTitle}>{riceTwo?.show}</Text>
            <Pressable
              onPress={() => setRiceTwo(play_dice())}
              style={styles.button}
            >
              <Text
                style={[
                  styles.text,
                  {
                    backgroundColor:
                      riceTwo?.show === "Dinamite" ? "red" : "blue",
                  },
                ]}
              >
                Dado 2
              </Text>
            </Pressable>
          </View>

          <View style={styles.card}>
            <Text style={styles.parentTitle}> {riceTree?.show}</Text>
            <Pressable
              onPress={() => setRiceTree(play_dice())}
              style={styles.button}
            >
              <Text
                style={[
                  styles.text,
                  {
                    backgroundColor:
                      riceTree?.show === "Dinamite" ? "red" : "blue",
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
