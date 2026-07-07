import { StatusBar, View } from "react-native";
// import Home from "./home";
import BangMatch from "./bangMatch";

const Index = () => {
    return (
        <View style={[{ marginTop: 40, flex: 1 }]}>
            <StatusBar barStyle="default" />
            <BangMatch />
        </View>
    );
};
export default Index;
