class GameNotFound(KeyError):
    """A partida nao existe (404)."""

    def __str__(self) -> str:
        return self.args[0] if self.args else "Partida nao encontrada"


class NotYourTurn(PermissionError):
    """Quem pediu a acao nao pode agir agora (403)."""


class StaleVersion(Exception):
    """A versao enviada nao bate com a atual: pedido repetido ou desatualizado (409)."""

    def __init__(self, current_version: int):
        super().__init__(f"Versao desatualizada. Versao atual: {current_version}")
        self.current_version = current_version
