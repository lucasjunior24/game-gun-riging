from pymongo import MongoClient
from app.controllers.base import BaseController
from app.dtos.match_game import MatchGameDTO


class GameController(BaseController[MatchGameDTO]):
    collection_name = "game"

    def __init__(
        self, dto: MatchGameDTO = MatchGameDTO, _client: MongoClient | None = None
    ):
        super().__init__(dto, _client)
