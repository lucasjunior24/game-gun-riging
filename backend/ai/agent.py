from ai.policy import HeuristicPolicy
from ai.schemas import GameState


class BangAgent:

    def __init__(self):
        self.policy = HeuristicPolicy()

    def decide(self, state: GameState):

        # 🎭 Ajustes por personagem antes da decisão
        state = self.apply_character_ability(state)

        return self.policy.choose_action(state)

    def apply_character_ability(self, state: GameState) -> GameState:

        # 🎭 Exemplos reais do jogo:

        if state.personagem == "Luke":
            # Luke pode rerollar um dado extra
            state.rerolls_restantes = min(3, state.rerolls_restantes + 1)

        if state.personagem == "Jack":
            # Jack pode ignorar dinamite (simulação simples)
            state.dados = ["normal" if d == "dynamite" else d for d in state.dados]

        if state.personagem == "Suzy":
            # Se não tiver tiros → ganha reroll agressivo
            if "tiro" not in state.dados:
                state.rerolls_restantes += 1

        return state
