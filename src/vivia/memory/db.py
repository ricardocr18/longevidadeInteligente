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


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(Path(settings.database_url))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Cria as tabelas se ainda não existirem. Roda automaticamente no
    boot da aplicação (ver web/app.py) — importante para o Railway,
    onde o volume persistente pode estar vazio no primeiro deploy, sem
    depender de alguém rodar scripts/seed_db.py manualmente por lá.

    Idempotente: rodar de novo num banco que já tem as tabelas não
    faz nada (CREATE TABLE IF NOT EXISTS), então é seguro chamar isso
    toda vez que a aplicação inicia, local ou em produção.
    """
    conn = get_connection()
    conn.execute(CREATE_MESSAGES)
    conn.execute(CREATE_SUMMARIES)
    conn.commit()
    conn.close()