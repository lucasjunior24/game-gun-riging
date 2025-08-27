import { Dimensions, View } from "react-native";
import { Image, useImage } from "expo-image";

import { characters } from "@/app/consts/characters";
export default function CircularList() {
  const image = useImage(characters[0].avatar as string, {
    maxWidth: 800,
    onError(error) {
      console.error("Loading failed:", error.message);
    },
  });

  return (
    <View
      style={{
        justifyContent: "center",
        alignItems: "center",
        paddingTop: 20,
        // padding: 15,
      }}
    >
      <View
        style={{
          borderRadius:
            Math.round(
              Dimensions.get("window").width + Dimensions.get("window").height
            ) / 2,
          width: Dimensions.get("window").width * 0.8,
          height: Dimensions.get("window").width * 0.8,
          borderWidth: 5,
          borderColor: "red",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <Image
          source={image}
          contentFit="cover"
          transition={1000}
          style={{
            height: 50,
            width: 50,
            position: "absolute",
            bottom: Dimensions.get("window").width * 0.7,
          }}
        />

        <Image
          source={image}
          style={{
            height: 50,
            width: 50,
            position: "absolute",
            bottom: Dimensions.get("window").width * 0.6,
            right: 20,
          }}
        />
        <Image
          source={image}
          style={{
            height: 50,
            width: 50,
            position: "absolute",
            bottom: Dimensions.get("window").width * 0.6,
            left: 20,
          }}
        />
        <Image
          source={image}
          style={{
            height: 50,
            width: 50,
            position: "absolute",
            top: Dimensions.get("window").width * 0.7,
          }}
        />
        <Image
          source={image}
          style={{
            height: 50,
            width: 50,
            position: "absolute",
            top: Dimensions.get("window").width * 0.6,
            right: 20,
          }}
        />
        <Image
          source={image}
          style={{
            height: 50,
            width: 50,
            position: "absolute",
            top: Dimensions.get("window").width * 0.6,
            left: 20,
          }}
        />
        <Image
          source={image}
          style={{
            height: 50,
            width: 50,
            position: "absolute",
            bottom: Dimensions.get("window").width * 0.3,
            left: -20,
          }}
        />
        <Image
          source={image}
          style={{
            height: 50,
            width: 50,
            position: "absolute",
            bottom: Dimensions.get("window").width * 0.3,
            right: -20,
          }}
        />
      </View>
    </View>
  );
}
