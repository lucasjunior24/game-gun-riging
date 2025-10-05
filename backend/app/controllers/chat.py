from app.controllers.base import BaseController
from app.db.models.chat import ChatDTO
from app.db.models.message import MessageDTO
from app.dtos.character import IdentityDTO
from app.dtos.dice import DiceShowDTO
from app.modelo.chat_bot import chat
import json


class ChatController(BaseController[ChatDTO]):
    collection_name = "chat"

    def __init__(self, dto: ChatDTO = ChatDTO):
        super().__init__(dto)

    def add_message(self, new_message: str, chat_id: str | None = None):
        chat_dto = self.get_by_id(id=chat_id) if chat_id else ChatDTO(user_id="lucas")
        messages = []
        if chat_id is None:
            messages_setup = self.run_setup()
            for message in messages_setup:
                messages.append({"role": "system", "content": message})

        for m in chat_dto.messages:
            if m.author == "agent":
                messages.append({"role": "assistant", "content": m.message})
                messages.append({"role": "assistant", "content": m.message})
            else:
                messages.append({"role": "user", "content": m.message})

        response_chat = chat(new_message, messages)
        python_dict = json.loads(response_chat)
        # return python_dict
        chat_user = MessageDTO(message=new_message, author="user")
        chat_agent = MessageDTO(message=response_chat, author="agent")
        chat_dto.messages.append(chat_user)
        chat_dto.messages.append(chat_agent)

        # data = self.create(chat_dto)
        return python_dict

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

    @staticmethod
    def format_message(
        personagem: str,
        user_name: str,
        dices: list[DiceShowDTO],
        playes_one: list[str],
        playes_two: list[str],
    ):
        one = 0
        two = 0
        m = "Voçê acabou de rolar os dados e tirou "
        for dice in dices:
            if dice.show == "1":
                one += 1
            if dice.show == "2":
                two += 1
        if one:
            m += f"{one} tiros de 1, e pode atirar ao no {playes_one[0]} ou no {playes_one[1]}"
            if two:
                m = (
                    +f"e {two} tiros de 2, e pode atirar ao no {playes_two[0]} ou no {playes_two[1]}"
                )
        elif two:
            m += f"{two} tiros de 2,  e pode atirar ao no {playes_two[0]} ou no {playes_two[1]}"

        message = (
            f"Voce é o jogador {user_name} do Jogo Bang Dice Game, seu personagem é o {personagem}. "
            + m,
        )
        return message

    @staticmethod
    def run_setup() -> list[str]:
        messages: list[str] = []
        initial_message = "Voçê é um agente especialista em no Jogo Bang Dice Game. A partida vai começar agora e tem 5 jogadores, sendo eles: Pedro que é o Xerife, seguindo a ordem vem o Lucas, Murilo, Aragão e o Roberto."
        messages.append(initial_message)
        return messages

    @staticmethod
    def run_bollets(personagem: str, user_name: str) -> list[str]:
        message = f"Voçê é um agente especialista em no Jogo Bang Dice Game, seu nome é {user_name} do Jogo Bang Dice Game, seu personagem é o {personagem}, Voçê acabou de rolar os dados e tirou 3 tiros de 1 distancia, em um dos seu lados está o Xerife e no outro lado o Aragão que ainda não jogou, responda apenas dizendo em quem vai ser o tiro e o total de tiros"
        return message

    @staticmethod
    def format_message_execution(
        personagem: str,
        user_name: str,
        dice: str,
        dices_total: str,
        playes_one: list[str],
        playes_two: list[str],
    ):
        m = "Voçê acabou de rolar os dados e tirou "
        if dice == "1":
            m += f"{dices_total} tiros de {dice} distancia, e pode atirar ao no {playes_one[0]} ou no {playes_one[1]}. "
            if dice == "2":
                m = (
                    +f"e {dice} tiros de {dice} distancia, e pode atirar ao no {playes_two[0]} ou no {playes_two[1]}"
                )
        elif dice == "2":
            m += f"{dice} tiros de {dice} distancia, e pode atirar ao no {playes_two[0]} ou no {playes_two[1]}"

        message = f"Voce é o jogador {user_name} do Jogo Bang Dice Game, seu personagem é o {personagem}. {m} Responda apenas dizendo em quem vai ser o tiro e o total de tiros."

        return message

    @staticmethod
    def format_message_dices(
        personagem: str,
        user_name: str,
        dice: str,
        dices_total: str,
        players: list[str],
    ):
        m = f"Voçê acabou de rolar os dados e tirou {dices_total} tiros de {dice} distancia, e pode atirar ao no {players[0]} ou no {players[1]}."
        message = f"Voce é o jogador {user_name} do Jogo Bang Dice Game, seu personagem é o {personagem}. {m} Responda apenas dizendo em quem vai ser o tiro e o total de tiros."

        return message
