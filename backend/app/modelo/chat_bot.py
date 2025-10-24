from litellm import completion


from app.dtos.dice import ListShotsDTO
from app.util.config import GROQ_API_KEY


def chat(user_message: str, messages: list | None = None):
    messages.append({"role": "user", "content": user_message})
    # Chamar a API com o histórico completo
    model_response = call_groq_api(messages)
    return model_response


def call_groq_api(messages, model="groq/llama-3.3-70b-versatile"):
    global tools
    question = messages[len(messages) - 3 : len(messages)]
    messagess = messages[0 : len(messages) - 1]
    response = completion(
        model=model,
        messages=question,
        api_key=GROQ_API_KEY,
        response_format=ListShotsDTO,
        metadata={"messages": messagess},
    )
    resposta_texto = response.choices[0].message
    # print(resposta_texto)
    return resposta_texto.content
