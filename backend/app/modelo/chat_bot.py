from litellm import completion

from app.util.config import GROQ_API_KEY


def chat(user_message: str, messages: list | None = None):
    print("Iniciando chat com o modelo. Digite 'sair' para encerrar.")
    message_initial = [
        {
            "role": "system",
            "content": """
    Você é o Chat da Terra e do Universo e responde em português brasileiro
    perguntas sobre a previsão do tempo na Terra e do espaço próximo à Terra, além de informações sobre terremotos.
    """,
        }
    ]
    list_message = messages if messages else message_initial

    while True:
        if user_message.lower() == "sair":
            print("Encerrando chat. Até a próxima!")
            break

        # Adicionar a mensagem do usuário ao histórico
        list_message.append({"role": "user", "content": user_message})
        # Chamar a API com o histórico completo
        model_response = call_groq_api(list_message)

        list_message.append({"role": "assistant", "content": model_response})
        # print("Assistent: ", model_response)
        # Adicionar a resposta do modelo ao histórico

        print()
        return model_response


def call_groq_api(messages, model="groq/llama-3.3-70b-versatile"):
    global tools
    response = completion(
        model=model,
        messages=messages,
        api_key=GROQ_API_KEY,
    )
    resposta_texto = response.choices[0].message
    # print(resposta_texto)
    return resposta_texto.content
