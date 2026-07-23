import sqlite3
from pathlib import Path

from vivia.config import settings


CREATE_MESSAGES = """
CREATE TABLE IF NOT EXISTS messages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT    NOT NULL,
    session_date TEXT    NOT NULL,
    moment       TEXT    NOT NULL,
    role         TEXT    NOT NULL,
    content      TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_SUMMARIES = """
CREATE TABLE IF NOT EXISTS daily_summaries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT    NOT NULL,
    summary_date TEXT    NOT NULL,
    summary      TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, summary_date)
);
"""


def seed() -> None:
    db_path = Path(settings.database_url)
    conn = sqlite3.connect(db_path)

    conn.execute(CREATE_MESSAGES)
    conn.execute(CREATE_SUMMARIES)
    conn.commit()
    conn.close()

    print(f"Banco criado em: {db_path.resolve()}")
    print("Tabelas: messages, daily_summaries")


if __name__ == "__main__":
    seed()