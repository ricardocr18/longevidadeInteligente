import sqlite3
from pathlib import Path
from vivia.config import settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(Path(settings.database_url))
    conn.row_factory = sqlite3.Row
    return conn