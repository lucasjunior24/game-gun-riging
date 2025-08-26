import { Modal, View, Text, Pressable, StyleSheet } from "react-native";
import { PropsWithChildren, useEffect, useMemo, useState } from "react";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Player } from "@/app/consts/players";
import { players_to_shot } from "@/app/game/shoot";

import { ButtonBase } from "../buttonBase";

import { DiceCombinationUndefined } from "@/app/consts/dice";

import ListShoots from "./listShoots";

type ShootProps = PropsWithChildren<{
  isVisible: boolean;
  onClose: () => void;
  playerMoment: number;
  playerName: string;
  players: Player[];
  shoots: DiceCombinationUndefined[];
  handleSetPlayers(players: Player[]): void;
  handleSetPlayer(playerMoment: number): void;
}>;

function definirTiros(
  state: number,
  playerName: string,
  players: Player[],
  player: Player,
  handleSetPlayers: (players: Player[]) => void,
  handleSetPlayer: (playerMoment: number) => void
): number {
  if (state > 0) {
    const new_players = players
      .map((p) => {
        if (p.user_id === player.user_id && p.bullet) {
          p.bullet -= 1;
          if (p.bullet === 0) {
            return;
          }
          return p;
        }
        return p;
      })
      .filter((p) => p !== undefined);
    const index = new_players.findIndex((p) => p.user_name === playerName);

    console.log("new index: ", index);
    handleSetPlayers(new_players);
    handleSetPlayer(index);
    return state - 1;
  }
  return state;
}

export default function Shoot({
  isVisible,
  onClose,
  playerMoment,
  players,
  shoots,
  playerName,
  handleSetPlayers,
  handleSetPlayer,
}: ShootProps) {
  const livePlayers = players;

  const optionsOneShoot = players_to_shot(
    playerMoment + 1,
    livePlayers.length,
    1
  );

  console.log("playerMoment ", playerMoment);
  console.log("livePlayers ", livePlayers.length);
  console.log(optionsOneShoot);
  // console.log(optionsOneShoot);
  // const optionsTwoShoot = players_to_shot(playerMoment, livePlayers.length, 2);

  const playersOneShot = useMemo(() => {
    return optionsOneShoot
      .map((index) => livePlayers.find((user, i) => i === index))
      .filter((p) => p !== undefined)
      .filter((p) => p.user_name !== playerName);
  }, [livePlayers, optionsOneShoot, playerName]);

  console.log(
    playersOneShot.map((p) => {
      return p.user_name;
    })
  );

  // console.log("playersOneShot, ", playersOneShot);
  // const playersTwoShot = useMemo(() => {
  //   return livePlayers.filter((p) => {
  //     if (optionsTwoShoot.find((user) => user === p.user_id)) {
  //       return p;
  //     }
  //   });
  // }, [optionsTwoShoot, livePlayers]);

  const oneShotTotal = useMemo(() => {
    return shoots.filter((s) => s?.show === "1").length;
  }, [shoots]);

  // const twoShotTotal = useMemo(() => {
  //   return shoots.filter((s) => s?.show === "2").length;
  // }, [shoots]);

  const [bulletOne, setBulletOne] = useState(0);
  // const [bulletTwo, setBulletTwo] = useState(0);
  useEffect(() => {
    if (oneShotTotal) {
      setBulletOne(oneShotTotal);
    }
  }, [oneShotTotal]);

  // useEffect(() => {
  //   if (twoShotTotal) {
  //     setBulletTwo(twoShotTotal);
  //   }
  // }, [twoShotTotal]);

  function handleOneBullet(player: Player) {
    setBulletOne((state) => {
      return definirTiros(
        state,
        playerName,
        livePlayers,
        player,
        handleSetPlayers,
        handleSetPlayer
      );
    });
  }

  // function handleTwoBullet(player: Player) {
  //   setBulletTwo((state) => {
  //     return definirTiros(state, livePlayers, player, handleSetPlayers);
  //   });
  // }

  return (
    <View>
      <Modal animationType="slide" transparent visible={isVisible} focusable>
        <View style={styles.modalContent}>
          <View style={styles.titleContainer}>
            <Text />
            <Text style={styles.title}>Dar tiros</Text>
            <Pressable onPress={onClose}>
              <MaterialIcons name="close" color={"#000"} size={26} />
            </Pressable>
          </View>

          <ListShoots
            distance={1}
            bullet={bulletOne}
            bulletTotal={oneShotTotal}
            handleTwoBullet={handleOneBullet}
            playersTwoShot={playersOneShot}
          />
          {/* <ListShoots
            distance={2}
            bullet={bulletTwo}
            bulletTotal={twoShotTotal}
            handleTwoBullet={handleTwoBullet}
            playersTwoShot={playersTwoShot}
          /> */}

          <View style={{ padding: 10, paddingTop: 20 }}>
            <ButtonBase onPress={onClose} text="Executar" />
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  modalContent: {
    width: "100%",

    borderTopRightRadius: 18,
    borderTopLeftRadius: 18,

    flexDirection: "column",

    justifyContent: "space-between",
    // padding: 10,
    backgroundColor: "#fff",
    position: "absolute",
    // height: 400,
    borderColor: "#000",
    borderStyle: "solid",
    borderWidth: StyleSheet.hairlineWidth,
    bottom: -10,
    borderRadius: 20,
    paddingBottom: 20,
  },
  titleContainer: {
    height: 60,
    width: "100%",
    borderTopRightRadius: 10,
    borderTopLeftRadius: 10,
    paddingHorizontal: 20,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: {
    color: "blue",
    fontSize: 18,
    fontWeight: "bold",
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
});
