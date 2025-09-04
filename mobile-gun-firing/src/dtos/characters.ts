export type Character = {
    //pergonagem
    initial_bullet: number;
    power: string;
    character: string;
    avatar: string;
};

export type Identity = "Xerife" | "Fora da lei" | "Renegado" | "Assistente";

export type Team = Exclude<Identity, "Assistente">;
