"""
Database layer for email agent.
Uses SQLite via Python's built-in sqlite3 — no extra dependencies.
Stores processed email results for the UI to query.
"""
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from app.config import settings

logger = logging.getLogger("email-agent.database")

DB_PATH: Path = settings.DATA_DIR / "digest.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row factory set."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row   # rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections with auto-commit/rollback."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("Database error: %s", e)
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Create all tables if they don't exist.
    Safe to call on every startup.
    """
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at      TEXT NOT NULL,
                email_count INTEGER NOT NULL DEFAULT 0,
                action_count INTEGER NOT NULL DEFAULT 0,
                ads_count   INTEGER NOT NULL DEFAULT 0,
                error_count INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS emails (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER NOT NULL REFERENCES runs(id),
                message_id      TEXT NOT NULL,
                subject         TEXT NOT NULL,
                sender          TEXT NOT NULL,
                date            TEXT,
                snippet         TEXT,
                body            TEXT,
                category        TEXT,
                confidence      REAL,
                reasoning       TEXT,
                summary         TEXT,
                requires_action INTEGER DEFAULT 0,
                action_type     TEXT,
                action_detail   TEXT,
                deadline        TEXT,
                skipped         INTEGER DEFAULT 0,
                error           TEXT,
                created_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_emails_run_id
                ON emails(run_id);

            CREATE INDEX IF NOT EXISTS idx_emails_category
                ON emails(category);

            CREATE INDEX IF NOT EXISTS idx_emails_message_id
                ON emails(message_id);

            CREATE INDEX IF NOT EXISTS idx_emails_created_at
                ON emails(created_at);

            CREATE TABLE IF NOT EXISTS drafts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id        INTEGER NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
                message_id      TEXT NOT NULL,
                subject         TEXT NOT NULL,
                recipient       TEXT NOT NULL,
                body            TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'pending',
                created_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id        INTEGER NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
                title           TEXT NOT NULL,
                description     TEXT,
                priority        TEXT NOT NULL DEFAULT 'medium',
                deadline        TEXT,
                status          TEXT NOT NULL DEFAULT 'todo',
                created_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS calendar_events (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id        INTEGER NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
                title           TEXT NOT NULL,
                description     TEXT,
                start_time      TEXT NOT NULL,
                end_time        TEXT,
                status          TEXT NOT NULL DEFAULT 'pending',
                event_id        TEXT,
                created_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_drafts_email_id ON drafts(email_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_email_id ON tasks(email_id);
            CREATE INDEX IF NOT EXISTS idx_calendar_events_email_id ON calendar_events(email_id);
        """)
    logger.info("Database initialized at %s", DB_PATH)