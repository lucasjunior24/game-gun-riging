import { View, Text, StyleSheet } from "react-native";
import { Image, useImage } from "expo-image";

import { Player } from "@/app/consts/players";
import { ButtonIcon } from "../buttonIcon";
import { userBullets } from "../shoot";
import { Dispatch } from "react";

type ShootProps = {
  player: Player;
  shoots: number;
  userBullets: userBullets[];
  setUser: Dispatch<React.SetStateAction<userBullets[]>>;
};

export default function CardShoot({
  player,
  shoots,
  userBullets,

  setUser,
}: ShootProps) {
  const image = useImage(player.character?.avatar as string, {
    maxWidth: 800,
    onError(error) {
      console.error("Loading failed:", error.message);
    },
  });

  if (!image) {
    return <Text>Image is loading...</Text>;
  }

  const user = userBullets.find((u) => u.index === player.user_name);
  const totalShot = userBullets.map((u) => u.shoots);
  const sumTotalShot = totalShot.reduce(
    (accumulator, currentValue) => accumulator + currentValue,
    0
  );

  return (
    <View
      style={[
        styles.parentItem,
        { backgroundColor: player.identity === "Xerife" ? "yellow" : "white" },
      ]}
    >
      <View>
        {player.character?.avatar && (
          <Image
            style={styles.image}
            source={image}
            contentFit="cover"
            transition={1000}
          />
        )}
      </View>
      <View style={styles.player}>
        <View style={{ width: 180 }}>
          <Text style={styles.parentTitle}>
            {player.user_name} - {player.identity}
          </Text>
          <Text style={styles.character}>
            {player.character?.character} - {player.bullet}
          </Text>
        </View>
        <View
          style={{
            flexDirection: "row",
            width: 70,
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <View style={{ width: 40 }}>
            <ButtonIcon
              disabled={shoots === sumTotalShot}
              onPress={() => {
                setUser((state) => {
                  const users = state.map((u) => {
                    if (u.index === player.user_name) {
                      u.shoots += 1;
                      return u;
                    }
                    return u;
                  });
                  if (users.length && user) {
                    return users;
                  }
                  return [
                    ...state,
                    {
                      index: player.user_name,
                      shoots: 1,
                    },
                  ];
                });
              }}
              text={` + ${shoots} `}
            />
          </View>
          {user && <Text style={styles.character}>- {user.shoots}</Text>}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  parentItem: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#ccc",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  parentTitle: {
    fontSize: 18,
    fontWeight: "bold",
  },
  image: {
    height: 60,
    width: 60,
    backgroundColor: "#0553",
  },
  player: {
    width: "100%",
    paddingLeft: 15,
    flexDirection: "row",
  },
  character: {
    fontSize: 14,
    fontWeight: "500",
  },
});
