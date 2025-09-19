import { StatusBar, View } from "react-native";
import Home from "./home";

const Index = () => {
    return (
        <View style={[{ marginTop: 40, flex: 1 }]}>
            <StatusBar barStyle="default" />
            <Home />
        </View>
    );
};
export default Index;
