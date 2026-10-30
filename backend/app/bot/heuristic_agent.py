from app.bot.agent import Decision
from app.dtos.character import IdentityDTO
from app.engine.dice import DiceFace
from app.engine.rules import RESOLUTION_ORDER, TARGETED_FACES, Assignment
from app.engine.view import PlayerObservation

XERIFE = IdentityDTO.XERIFE
ASSISTENTE = IdentityDTO.ASSISTENTE
RENEGADO = IdentityDTO.RENEGADO
FORA_DA_LEI = IdentityDTO.FORA_DA_LEI


class HeuristicAgent:
    """O bot provisorio da Fase 1 como `Agent`: regras fixas, sem crenca nem busca.

    Serve de referencia nas comparacoes da Fase 5. Tambem so le a observacao:
    a versao antiga lia o papel real dos outros, o que nao e justo numa comparacao.

    - rola de novo Flechas, e Cervejas quando esta com a vida cheia;
    - atira no Xerife se for Fora da lei; senao, no alvo com menos vida (nunca no Xerife
      sendo do time dele, e so no Xerife sendo Renegado quando nao ha outro alvo);
    - Assistente e Renegado dao Cerveja ao Xerife ferido se tiverem mais de 2 de vida.
    """

    def __init__(self, seed: int | None = None, name: str = "heuristic"):
        self.name = name  # `seed` existe so para ter a mesma assinatura dos outros agentes

    def choose_reroll(self, obs: PlayerObservation) -> Decision[set[int] | None]:
        me = obs.players[obs.viewer_seat]
        reroll = {
            d.index
            for d in obs.dice
            if d.face is DiceFace.ARROW or (d.face is DiceFace.BEER and me.life == me.max_life)
        }
        if not reroll:
            return Decision(None, 0.0, 1.0, "Parou de rolar")
        return Decision(reroll, 0.0, 1.0, "Rolou de novo Flechas e Cervejas inuteis")

    def choose_assignments(self, obs: PlayerObservation) -> Decision[list[Assignment]]:
        # O runner pede um plano novo quando alguem morre, entao os alvos validos e as
        # distancias da observacao valem para o plano inteiro. Vidas mudam: guardamos aqui.
        life = {p.seat: p.life for p in obs.players}
        pending = [d for d in obs.dice if d.face in TARGETED_FACES and not d.resolved]
        pending.sort(key=lambda d: (RESOLUTION_ORDER[d.face], d.index))
        plan = []
        for die in pending:
            targets = valid_targets(obs, die.face)
            if die.face is DiceFace.BEER:
                target = self._beer_target(obs, targets, life)
                life[target] = min(obs.players[target].max_life, life[target] + 1)
            else:
                target = self._shot_target(obs, targets, life)
                life[target] = max(0, life[target] - 1)
            plan.append(Assignment(dice_index=die.index, target_seat=target))
        return Decision(plan, 0.0, 1.0, "Regra fixa: Xerife ou quem tem menos vida")

    def _shot_target(self, obs: PlayerObservation, targets: list[int], life: dict[int, int]) -> int:
        sheriff = _sheriff(obs)
        if obs.my_identity is FORA_DA_LEI:
            if sheriff in targets:
                return sheriff
        else:
            targets = [t for t in targets if t != sheriff] or targets
        return min(targets, key=lambda t: (life[t], t))

    def _beer_target(self, obs: PlayerObservation, targets: list[int], life: dict[int, int]) -> int:
        me = obs.viewer_seat
        sheriff = _sheriff(obs)
        if obs.my_identity in (ASSISTENTE, RENEGADO) and sheriff in targets:
            hurt = life[sheriff] < obs.players[sheriff].max_life
            if hurt and life[me] > 2:
                return sheriff
        return me


def valid_targets(obs: PlayerObservation, face: DiceFace) -> list[int]:
    """O mesmo que `app.engine.seating.valid_targets`, mas lendo a observacao."""
    alive = [p for p in obs.players if p.is_alive]
    if face is DiceFace.BEER:
        return [p.seat for p in alive]
    wanted = 1 if face is DiceFace.SHOT_1 or len(alive) <= 3 else 2
    return [
        p.seat
        for p in alive
        if p.seat != obs.viewer_seat and p.distance_from_viewer == wanted
    ]


def _sheriff(obs: PlayerObservation) -> int | None:
    return next((p.seat for p in obs.players if p.public_identity is XERIFE), None)
