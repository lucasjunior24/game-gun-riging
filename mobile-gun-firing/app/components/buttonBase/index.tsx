import { StyleSheet, Text, Pressable } from "react-native";

interface ButtonBaseProps {
  text: string;
  color?: string;
  disabled?: boolean;
  onPress: () => void;
}

export const ButtonBase = ({
  text,
  onPress,
  color = style.buttonPay.backgroundColor,
  disabled = false,
}: ButtonBaseProps) => {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        style.buttonPay,
        { backgroundColor: color, opacity: disabled ? 0.7 : 1 },
      ]}
    >
      <Text style={style.buttonText}>{text}</Text>
    </Pressable>
  );
};
const style = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
    paddingHorizontal: 8,
  },

  buttonPay: {
    backgroundColor: "blue",
    borderRadius: 8,
    color: "#fff",
    height: 48,
    alignItems: "center",
    justifyContent: "center",
  },
  buttonText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "500",
  },
});
