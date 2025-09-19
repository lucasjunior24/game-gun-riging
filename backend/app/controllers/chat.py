from app.controllers.base import BaseController
from app.db.models.chat import ChatDTO
from app.db.models.message import MessageDTO
from app.dtos.character import IdentityDTO
from app.dtos.dice import DiceShowDTO
from app.modelo.chat_bot import chat


class ChatController(BaseController[ChatDTO]):
    collection_name = "chat"

    def __init__(self, dto: ChatDTO = ChatDTO):
        super().__init__(dto)

    def add_message(self, message: str, chat_id: str | None) -> ChatDTO:
        chat_dto = self.get_by_id(id=chat_id) if chat_id else ChatDTO(user_id="lucas")
        messages = []
        for m in chat_dto.messages:
            if m.author == "agent":
                messages.append({"role": "assistant", "content": m.message})
            else:
                messages.append({"role": "user", "content": m.message})

        response_chat = chat(message, messages)

        chat_user = MessageDTO(message=message, author="user")
        chat_agent = MessageDTO(message=response_chat, author="agent")
        chat_dto.messages.append(chat_user)
        chat_dto.messages.append(chat_agent)

        data = self.create(chat_dto)
        return data

    def formart_to_execure_dices(
        self,
        identity: IdentityDTO,
        dices: list[DiceShowDTO],
        chat_id: str | None,
    ):
        chat_dto = self.get_by_id(id=chat_id) if chat_id else ChatDTO(user_id="lucas")
        message = self.format_message(identity, dices)

        messages = []
        for m in chat_dto.messages:
            if m.author == "agent":
                messages.append({"role": "assistant", "content": m.message})
            else:
                messages.append({"role": "user", "content": m.message})

        response_chat = chat(message, messages)

        chat_user = MessageDTO(message=message, author="user")
        chat_agent = MessageDTO(message=response_chat, author="agent")
        chat_dto.messages.append(chat_user)
        chat_dto.messages.append(chat_agent)

        data = self.create(chat_dto)
        return data

    def format_message(
        self,
        identity: IdentityDTO,
        dices: list[DiceShowDTO],
    ):
        one = 0
        two = 0
        m = "Você acabou de rolar os dados e tirou "
        for dice in dices:
            if dice.show == "1":
                one += 1
            if dice.show == "2":
                two += 1
        if one:
            m += f"{one} tiros de 1, "
            if two:
                m = +f"e {two} tiros de 2, "
        elif two:
            m += f"{two} tiros de 2, "

        message_dices = (
            m
            + "em um dos seu lados está o Xerife e no outro lado um personagem que ainda não jogou, responda apenas dizendo em quem vai ser o tiro e o total de tiros"
        )
        message = f"Seu personagem sendo o {identity.value}," + message_dices
        return message
