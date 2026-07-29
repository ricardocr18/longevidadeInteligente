from datetime import date
from vivia.memory.db import get_connection


def save_message(
    user_id: str,
    moment: str,
    role: str,
    content: str,
    session_date: str | None = None,
) -> None:
    sd = session_date or date.today().isoformat()
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO messages (user_id, session_date, moment, role, content)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, sd, moment, role, content),
    )
    conn.commit()
    conn.close()


def get_today_messages(user_id: str, session_date: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT role, content
        FROM messages
        WHERE user_id = ? AND session_date = ?
        ORDER BY id ASC
        """,
        (user_id, session_date),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_today_messages(user_id: str, session_date: str) -> int:
    """
    Apaga as mensagens do dia de uma persona — usado pelo botão
    'Reiniciar conversa' na POC. Sem isso, a tela limpa mas o próximo
    turno recarrega o histórico do banco e a conversa 'volta' de onde
    parou, porque _process_turn sempre reconstrói o contexto a partir
    do SQLite, não da memória do navegador.

    Só afeta o dia de hoje — dias anteriores continuam intactos, o que
    importa para os testes de memória entre dias da Fase 4.
    """
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM messages WHERE user_id = ? AND session_date = ?",
        (user_id, session_date),
    )
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def get_recent_summaries(user_id: str, days: int = 7) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT summary_date, summary
        FROM daily_summaries
        WHERE user_id = ?
        ORDER BY summary_date DESC
        LIMIT ?
        """,
        (user_id, days),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def format_summaries_for_prompt(summaries: list[dict]) -> str:
    if not summaries:
        return ""
    lines = []
    for s in reversed(summaries):
        lines.append(f"[{s['summary_date']}] {s['summary']}")
    return "\n".join(lines)