import React, { ReactNode } from "react";
import { StyleSheet, Pressable, Text } from "react-native";

interface ButtonBaseProps {
  children?: ReactNode;
  color?: string;
  disabled?: boolean;
  onPress: () => void;
  text: string;
}

export const ButtonIcon = ({
  children,
  onPress,
  color = style.buttonPay.backgroundColor,
  disabled = false,
  text,
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
      {text && <Text style={style.buttonText}>{text}</Text>}
      {children && children}
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
