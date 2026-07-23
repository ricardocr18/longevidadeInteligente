from openai import OpenAI
from vivia.config import settings


def run() -> None:
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=256,
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é a Vivia, tutora de saúde de um programa de "
                    "longevidade inteligente para pessoas com 60 anos ou mais. "
                    "Seu tom é acolhedor, próximo e respeitoso."
                ),
            },
            {
                "role": "user",
                "content": "Apresente-se em uma frase.",
            },
        ],
    )

    print("\n── Vivia diz: ──────────────────────────")
    print(response.choices[0].message.content)
    print("────────────────────────────────────────\n")


if __name__ == "__main__":
    run()