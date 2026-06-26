import random

from ai.schemas import GameState, Player, Player

from ai.utils import build_attack_matrix, predict_incoming_damage


class HeuristicPolicy:

    def choose_action(self, state: GameState):
        # Fase 1: reroll
        if state.rerolls_restantes > 0:
            keep = self.choose_dice_to_keep(state)
            return {"action": "reroll", "keep": keep}

        # Fase 2: ação final
        return {"action": self.choose_final_action(state), "keep": []}

    # 🎲 Decide quais dados manter
    def choose_dice_to_keep(self, state: GameState):
        keep = []

        for i, d in enumerate(state.dados):

            # ❌ Dynamite nunca rerolla
            if d == "dynamite":
                keep.append(i)
                continue

            # ❤️ Baixa vida → segura cerveja
            if d == "cerveja" and state.vida <= 3:
                keep.append(i)
                continue

            # 🔫 Ataque → depende do papel
            if d == "tiro":
                if state.papel in ["fora_da_lei", "renegado"]:
                    keep.append(i)
                elif state.papel == "xerife" and state.inimigos_alcance:
                    keep.append(i)

            # 🔥 Gatling → sempre bom
            if d == "gatling":
                keep.append(i)

        return keep

    # 🔫 Decisão final
    def choose_final_action(self, state: GameState):

        dados = state.dados

        if dados.count("dynamite") >= 3:
            return "explodiu"

        if "cerveja" in dados and state.vida < state.vida_max:
            return "usar_cerveja"

        if dados.count("gatling") >= 3:
            return "usar_gatling"

        if "tiro" in dados:
            alvo = self.choose_target(state)
            if alvo is not None:
                return f"atacar_{alvo}"

        return "passar"

    # 🎯 Escolha de alvo (papel importa MUITO)
    def choose_target(self, state: GameState):
        attacks = build_attack_matrix(state.history)
        incoming = predict_incoming_damage(state)

        candidatos = [p for p in state.players if p.distancia <= 2 and p.vida > 0]

        scored = [
            (p, self.score_target(state, p, attacks, incoming)) for p in candidatos
        ]

        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0].id if scored else None

    def target_sheriff(self, state: GameState):
        # Simplificação: assume player 0 é xerife
        return 0

    def score_target(
        self,
        state: GameState,
        player: Player,
        attacks: dict[int, dict[int, int]],
        incoming: dict[int, int],
    ):

        score = 0

        # 🎭 Papel
        if state.papel == "fora_da_lei":
            if player.papel_estimado == "xerife":
                score += 10

        if state.papel == "xerife":
            if player.papel_estimado == "fora_da_lei":
                score += 8

        # 🔥 HISTÓRICO DE AGRESSÃO (ESSENCIAL)
        score += attacks[player.id][state.self_id] * 5  # vingança

        # 🧠 Se ele está sendo atacado por muitos → pode morrer sozinho
        score -= incoming[player.id] * 2

        # 🎯 Finalizar alvo
        if player.vida == 1:
            score += 6

        # 📏 Distância
        score += 3 - player.distancia

        return score
