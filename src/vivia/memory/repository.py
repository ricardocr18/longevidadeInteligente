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
    """
    Apesar do nome, funciona para QUALQUER data — usada tanto para
    reconstruir a conversa de hoje quanto para ler dias passados na
    hora de gerar o resumo diário (summarizer.py).
    """
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
    """Usado só pelo endpoint de reset de teste — protegido por test_mode."""
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM messages WHERE user_id = ? AND session_date = ?",
        (user_id, session_date),
    )
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def get_pending_summary_dates(
    user_id: str, before_date: str, min_messages: int = 4
) -> list[str]:
    """
    Encontra dias PASSADOS (antes de `before_date`, tipicamente hoje) que
    já têm conversa registrada mas ainda não têm resumo salvo — e que
    têm mensagens suficientes pra valer a pena resumir.

    É essa consulta que detecta 'a conversa está acontecendo num dia à
    frente' e decide se há algo pendente pra resumir antes de seguir.
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT m.session_date, COUNT(*) AS total
        FROM messages m
        LEFT JOIN daily_summaries d
            ON d.user_id = m.user_id AND d.summary_date = m.session_date
        WHERE m.user_id = ?
          AND m.session_date < ?
          AND d.id IS NULL
        GROUP BY m.session_date
        HAVING total >= ?
        ORDER BY m.session_date ASC
        """,
        (user_id, before_date, min_messages),
    ).fetchall()
    conn.close()
    return [r["session_date"] for r in rows]


def upsert_daily_summary(user_id: str, summary_date: str, summary: str) -> None:
    """
    Salva o resumo do dia. Usa UPSERT (INSERT ... ON CONFLICT) porque a
    tabela tem UNIQUE(user_id, summary_date) — se por algum motivo o
    resumo daquele dia já existir, atualiza em vez de duplicar ou falhar.
    """
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO daily_summaries (user_id, summary_date, summary)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, summary_date)
        DO UPDATE SET summary = excluded.summary, created_at = datetime('now')
        """,
        (user_id, summary_date, summary),
    )
    conn.commit()
    conn.close()


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