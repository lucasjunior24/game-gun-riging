// Player antigo REMOVIDO - usar PublicPlayer de gameState.ts
// Este arquivo agora re-exporta PublicPlayer para compatibilidade

export type PublicPlayer = {
    user_id: number;
    user_name: string;
    position: number;
    character?: import("./gameState").Character;
    is_alive: boolean;
    is_bot: boolean;
    arrow: number;
    bullet: number;
    revealed_identity?: import("./gameState").Identity; // SÓ o Xerife - nunca identidades ocultas
};

/**
 * @deprecated Usar PublicPlayer de gameState.ts
 * Alias mantido apenas para compatibilidade com arquivos obsoletos
 */
export type Player = PublicPlayer & {
    identity?: import("./gameState").Identity;
    team?: import("./gameState").Team;
};
