import React, { useState } from "react";
import { Player } from "@/app/consts/players";
import { DiceCombinationUndefined } from "@/app/consts/dice";
import { pass_player } from "@/app/game/init_game";
import { locked_dice, play_dice, sum_shoots } from "@/app/game/play_dice";
import { View, Text, StyleSheet, Pressable } from "react-native";
import Shoot from "../shoot";
import DiceItem from "./diceItem";

interface DicesProps {
  players: Player[];
  playerMoment: number;
  playerName: string;
  handleSetPlayers(players: Player[]): void;
  setPlayerMoment: (user_id: number, user_name: string) => void;
}

const Dices = ({
  players,
  playerMoment,
  playerName,
  handleSetPlayers,
  setPlayerMoment,
}: DicesProps) => {
  const [diceOne, setDiceOne] = useState<DiceCombinationUndefined>();
  const [diceTwo, setDiceTwo] = useState<DiceCombinationUndefined>();
  const [diceThree, setDiceThree] = useState<DiceCombinationUndefined>();
  const [diceFour, setDiceFour] = useState<DiceCombinationUndefined>();
  const [diceFive, setDiceFive] = useState<DiceCombinationUndefined>();

  const [openModal, setOpenModal] = useState(false);
  const [totalDiceRolls, setTotalDiceRolls] = useState(0);

  // const pl = players.indexOf(, playerMoment);
  // console.log("pl: ", pl);
  function passPlayer() {
    const new_pl = pass_player(playerMoment, players.length);
    const player = players[new_pl];

    setPlayerMoment(new_pl, player.user_name);
    setDiceOne(undefined);
    setDiceTwo(undefined);
    setDiceThree(undefined);
    setDiceFour(undefined);
    setDiceFive(undefined);
    setTotalDiceRolls(0);
  }
  function handleSetPlayer(playerMoment: number) {
    setPlayerMoment(playerMoment, playerName);
  }
  const player = players.filter((p) => p.user_name === playerName)[0];
  console.log("playerMoment: ", playerMoment);
  console.log(playerName);
  function playAllDices() {
    if (diceOne?.locked !== true) {
      setDiceOne(play_dice());
    }
    if (diceTwo?.locked !== true) {
      setDiceTwo(play_dice());
    }
    if (diceThree?.locked !== true) {
      setDiceThree(play_dice());
    }
    if (diceFour?.locked !== true) {
      setDiceFour(play_dice());
    }
    if (diceFive?.locked !== true) {
      setDiceFive(play_dice());
    }
    setTotalDiceRolls((state) => {
      return (state += 1);
    });
  }

  // function runMetralhadora() {
  //   const players_now = players.map((p) => {
  //     if (p.user_id === Number(playerMoment)) {
  //       return p;
  //     }
  //     if (p.character && p.bullet) {
  //       p.bullet -= 1;
  //     }
  //     return p;
  //   });
  //   handleSetPlayers(players_now);
  // }
  function exeDices() {
    // runMetralhadora();
    setOpenModal(true);
  }

  if (player === undefined) {
    return <Text>loading player...</Text>;
  }
  const sumShoots = sum_shoots(diceOne, diceTwo, diceThree, diceFour, diceFive);
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
              onPress={playAllDices}
              style={[
                styles.button,
                { backgroundColor: totalDiceRolls === 3 ? "red" : "blue" },
              ]}
              disabled={totalDiceRolls === 3}
            >
              <Text style={styles.text}>Play All Dices</Text>
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
              <Text style={styles.text}>Execute Dices</Text>
            </Pressable>
          </View>
        </View>
        <View style={styles.card}>
          <Text style={styles.parentTitle}>Dados travados</Text>
          <DiceItem
            dice={diceOne}
            handleDice={() => setDiceOne((state) => locked_dice(state))}
          />
          <DiceItem
            dice={diceTwo}
            handleDice={() => setDiceTwo((state) => locked_dice(state))}
          />
          <DiceItem
            dice={diceThree}
            handleDice={() => setDiceThree((state) => locked_dice(state))}
          />
          <DiceItem
            dice={diceFour}
            handleDice={() => setDiceFour((state) => locked_dice(state))}
          />
          <DiceItem
            dice={diceFive}
            handleDice={() => setDiceFive((state) => locked_dice(state))}
          />
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
          playerName={playerName}
          handleSetPlayer={handleSetPlayer}
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
