import {
  Modal,
  View,
  Text,
  Pressable,
  StyleSheet,
  FlatList,
} from "react-native";
import { PropsWithChildren, useEffect, useMemo, useState } from "react";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Player } from "@/app/consts/players";
import { players_to_shot } from "@/app/game/shoot";

import { ButtonBase } from "../buttonBase";

import { DiceCombinationUndefined } from "@/app/consts/dice";
import CardShoot from "../cardShoot";

type ShootProps = PropsWithChildren<{
  isVisible: boolean;
  onClose: () => void;
  playerMoment: string;
  players: Player[];
  shoots: DiceCombinationUndefined[];
  handleSetPlayers(players: Player[]): void;
  passPlayer(): void;
}>;

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
  // const optionsTwoShoot = players_to_shot(playerMoment, players.length, 2);
  const playersToShot = useMemo(() => {
    return players.filter((p) => {
      if (optionsOneShoot.find((user) => user === p.user_id)) {
        return p;
      }
    });
  }, [optionsOneShoot, players]);
  console.log("--------------------------");
  const shotOneDistance = useMemo(() => {
    return shoots.filter((s) => s?.show === "1").length;
  }, [shoots]);
  console.log("shotOneDistance", shotOneDistance);
  const [bullet, setBullet] = useState(shotOneDistance);
  useEffect(() => {
    if (shotOneDistance) {
      setBullet(shotOneDistance);
    }
  }, [shotOneDistance]);
  // const shotTwoDistance = shoots.filter((s) => s?.show === "2").length;

  console.log("bullet", bullet);

  function handleBullet(player: Player) {
    setBullet((state) => {
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
          <View>
            <Text style={styles.title}>1 Distancia = {shotOneDistance}</Text>
            {/* <Text style={styles.title}>2 Distancia = {shotTwoDistance}</Text> */}
          </View>
          <View>
            <FlatList
              data={playersToShot}
              renderItem={({ item }) => (
                <CardShoot
                  player={item}
                  shoots={bullet}
                  handleBullet={handleBullet}
                />
              )}
              keyExtractor={(item) => String(item.user_id)}
            />

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
    bottom: 20,
    borderRadius: 20,
    paddingBottom: 100,
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
