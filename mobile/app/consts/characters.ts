export type Character = {
    //pergonagem
    bullet: number;
    power: string;
    character: string;
};

export const characters: Character[] = [
    {
        bullet: 8,
        character: "Geni Calamidade",
        power: "Pode trocar a posição dos balso de tiro de 1 e 2 entre si",
    },
    {
        bullet: 7,
        character: "Gringo",
        power: "Se atirar nele, pega uma flecha",
    },
    {
        bullet: 9,
        character: "Esquiva Metralha",
        power: "Não toma tira de metralhadora",
    },
    {
        bullet: 7,
        character: "Duque sortudo",
        power: "Ganha um ponto de vida no inicio do turno",
    },
];

export type Identity = "Xerife" | "Fora da lei" | "Renegado" | "Assistente";
