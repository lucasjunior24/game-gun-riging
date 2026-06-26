import random

from ai.schemas import GameState, Player, Player

from ai.schemas import GameState


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
    def choose_target(self, state):

        candidatos = [p for p in state.players if p.distancia <= 2 and p.vida > 0]

        if not candidatos:
            return None

        scored = [(p, self.score_target(state, p)) for p in candidatos]

        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0].id

    def target_sheriff(self, state: GameState):
        # Simplificação: assume player 0 é xerife
        return 0

    def score_target(self, state: GameState, player: Player):

        score = 0

        # 🎭 Baseado no papel
        if state.papel == "fora_da_lei":
            if player.papel_estimado == "xerife":
                score += 10
            score += player.suspeita * 5

        elif state.papel == "xerife":
            if player.papel_estimado == "fora_da_lei":
                score += 8
            score += player.suspeita * 4

        elif state.papel == "renegado":
            # Quer equilibrar o jogo
            if player.papel_estimado == "xerife":
                score += 3
            else:
                score += 5

        elif state.papel == "vice":
            if player.papel_estimado == "fora_da_lei":
                score += 9

        # ❤️ Finalizar inimigo (muito importante)
        if player.vida == 1:
            score += 6

        # 📏 Distância (mais perto = melhor)
        score += 3 - player.distancia

        return score
