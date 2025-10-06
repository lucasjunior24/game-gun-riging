from pymongo import MongoClient
from app.controllers.base import BaseController
from app.dtos.history import HistoryDTO
from app.dtos.message import MessageDTO


class HistoryController(BaseController[HistoryDTO]):
    collection_name = "history"

    def __init__(
        self, dto: HistoryDTO = HistoryDTO, _client: MongoClient | None = None
    ):
        super().__init__(dto, _client)

    def add_messages(self, messages: list[MessageDTO], history_id: str) -> HistoryDTO:
        history = self.get_by_id(id=history_id)
        for message in messages:
            history.messages.append(message)

        history_save = self.update(history)
        return history_save

    def add_messages_by_game_id(
        self, messages: list[MessageDTO], game_id: str
    ) -> HistoryDTO:
        history = self.get_filter("game_id", game_id)
        for message in messages:
            history.messages.append(message)

        history_save = self.update(history)
        return history_save

    @staticmethod
    def create_messages_dto(messages: list[str]) -> list[MessageDTO]:
        messages_dto: list[MessageDTO] = []
        for message in messages:
            message_dto = MessageDTO(message=message, author="lucas-sousa")
            messages_dto.append(message_dto)

        return messages_dto
