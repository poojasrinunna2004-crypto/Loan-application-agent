import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "loan_agent.db"
DB_PATH = Path(os.environ.get("LOAN_AGENT_DB_PATH", str(_DEFAULT_DB_PATH)))


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                annual_income REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                loan_type TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                term_months INTEGER NOT NULL CHECK (term_months > 0),
                purpose TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft', 'submitted')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                submitted_at TEXT
            );
            INSERT OR IGNORE INTO customers (id, name, email, annual_income)
            VALUES
                (1, 'Jordan Lee', 'jordan.lee@example.test', 72000),
                (2, 'Taylor Morgan', 'taylor.morgan@example.test', 94500),
                (3, 'Casey Patel', 'casey.patel@example.test', 61000);
            """
        )
