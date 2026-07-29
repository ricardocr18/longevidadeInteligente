from pathlib import Path

from openai import OpenAI

from vivia.config import settings
from vivia.memory.repository import (
    get_today_messages,
    get_pending_summary_dates,
    upsert_daily_summary,
)

PROMPT_PATH = (
    Path(__file__).parent.parent.parent.parent / "data" / "prompts" / "summary_prompt.md"
)

MIN_MESSAGES_TO_SUMMARIZE = 4


def _load_prompt_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _format_conversation(rows: list[dict]) -> str:
    lines = []
    for r in rows:
        speaker = "Vivia" if r["role"] == "assistant" else "Pessoa"
        lines.append(f"{speaker}: {r['content']}")
    return "\n".join(lines)


def generate_summary_text(user_id: str, session_date: str) -> str | None:
    """
    Lê as mensagens de um dia específico e pede pro modelo condensar em
    um resumo curto, seguindo as prioridades do summary_prompt.md.
    Retorna None se não houver mensagens suficientes.
    """
    rows = get_today_messages(user_id, session_date)
    if len(rows) < MIN_MESSAGES_TO_SUMMARIZE:
        return None

    conversation_text = _format_conversation(rows)
    prompt = _load_prompt_template().format(
        user_id=user_id,
        session_date=session_date,
        conversation_text=conversation_text,
    )

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def ensure_summaries_up_to_date(
    user_id: str, before_date: str, min_messages: int = MIN_MESSAGES_TO_SUMMARIZE
) -> list[str]:
    """
    Checagem de virada de dia: procura dias passados desta persona que
    já têm conversa mas ainda não têm resumo, e gera o que estiver
    faltando antes de continuar. Roda a cada turno — é uma consulta
    barata, só vira trabalho de verdade quando há pendência de verdade.

    Retorna a lista de datas que foram resumidas nesta chamada (útil
    para logs e para os testes).
    """
    pending_dates = get_pending_summary_dates(user_id, before_date, min_messages)
    processed = []

    for pending_date in pending_dates:
        summary = generate_summary_text(user_id, pending_date)
        if summary:
            upsert_daily_summary(user_id, pending_date, summary)
            processed.append(pending_date)

    return processed