export type Rice = 1 | 2 | 3 | 4 | 5 | 6;

export type RiceOptions =
    | "1"
    | "2"
    | "Cerveja"
    | "Dinamite"
    | "Flexa"
    | "Flexa";

export type RiceCombination = {
    rice: Rice;
    show: RiceOptions;
};

export const RICES: RiceCombination[] = [
    { rice: 1, show: "1" },
    { rice: 2, show: "2" },
    { rice: 3, show: "Cerveja" },
    { rice: 4, show: "Dinamite" },
    { rice: 5, show: "Flexa" },
    { rice: 6, show: "Flexa" },
];
