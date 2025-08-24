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
  playerMoment: string;
  players: Player[];
  shoots: DiceCombinationUndefined[];
  handleSetPlayers(players: Player[]): void;
  passPlayer(): void;
}>;

function definirTiros(
  state: number,
  players: Player[],
  player: Player,
  handleSetPlayers: (players: Player[]) => void
): number {
  if (state > 0) {
    const new_players = players.map((p) => {
      if (p.user_id === player.user_id && p.character?.bullet) {
        p.character.bullet -= 1;
        return p;
      }
      return p;
    });
    handleSetPlayers(new_players);
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
  handleSetPlayers,
  passPlayer,
}: ShootProps) {
  const optionsOneShoot = players_to_shot(playerMoment, players.length, 1);
  const optionsTwoShoot = players_to_shot(playerMoment, players.length, 2);
  const playersOneShot = useMemo(() => {
    return players.filter((p) => {
      if (optionsOneShoot.find((user) => user === p.user_id)) {
        return p;
      }
    });
  }, [optionsOneShoot, players]);

  const playersTwoShot = useMemo(() => {
    return players.filter((p) => {
      if (optionsTwoShoot.find((user) => user === p.user_id)) {
        return p;
      }
    });
  }, [optionsTwoShoot, players]);

  const shotOneDistance = useMemo(() => {
    return shoots.filter((s) => s?.show === "1").length;
  }, [shoots]);

  const shotTwoDistance = useMemo(() => {
    return shoots.filter((s) => s?.show === "2").length;
  }, [shoots]);

  const [bulletOne, setBulletOne] = useState(0);
  const [bulletTwo, setBulletTwo] = useState(0);
  useEffect(() => {
    if (shotOneDistance) {
      setBulletOne(shotOneDistance);
    }
  }, [shotOneDistance]);

  useEffect(() => {
    if (shotTwoDistance) {
      setBulletTwo(shotTwoDistance);
    }
  }, [shotTwoDistance]);

  function handleOneBullet(player: Player) {
    setBulletOne((state) => {
      return definirTiros(state, players, player, handleSetPlayers);
    });
  }

  function handleTwoBullet(player: Player) {
    setBulletTwo((state) => {
      return definirTiros(state, players, player, handleSetPlayers);
    });
  }
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
            shotTwoDistance={shotOneDistance}
            bulletTwo={bulletOne}
            handleTwoBullet={handleOneBullet}
            playersTwoShot={playersOneShot}
          />
          <ListShoots
            shotTwoDistance={shotTwoDistance}
            bulletTwo={bulletTwo}
            handleTwoBullet={handleTwoBullet}
            playersTwoShot={playersTwoShot}
          />

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
