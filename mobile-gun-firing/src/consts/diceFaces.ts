import { DiceFace } from "../dtos/gameView";

// Só desenho: o que cada face faz é decidido pelo servidor.
export const FACE_ICON: Record<DiceFace, string> = {
    "1": "①",
    "2": "②",
    Dinamite: "🧨",
    Cerveja: "🍺",
    Flecha: "🏹",
    Metralhadora: "💥",
};

export function faceIcon(face: string | null | undefined): string {
    if (!face) return "🎲";
    return FACE_ICON[face as DiceFace] ?? face;
}
