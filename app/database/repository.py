"""
Repository layer — all database read/write operations.
Keeps SQL out of the rest of the codebase.
"""
import logging
from datetime import datetime, timezone
from app.schemas import EmailState
from app.database.db import get_db

logger = logging.getLogger("email-agent.repository")


# ── Write operations ──────────────────────────────────────────────────────────

def save_run(results: list[EmailState], run_at: datetime | None = None) -> int:
    """
    Save a complete agent run and all its email results to the database.

    Args:
        results: List of enriched EmailState dicts from the agent.
        run_at:  Timestamp of the run (defaults to now).

    Returns:
        The run_id of the inserted run.
    """
    run_at = run_at or datetime.now(timezone.utc)

    action_count = sum(1 for r in results if r.get("requires_action"))
    ads_count    = sum(1 for r in results if r.get("category") == "ads")
    error_count  = sum(1 for r in results if r.get("error"))

    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO runs (run_at, email_count, action_count, ads_count, error_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_at.isoformat(), len(results), action_count, ads_count, error_count),
        )
        run_id = cursor.lastrowid

        for r in results:
            cursor = conn.execute(
                """
                INSERT INTO emails (
                    run_id, message_id, subject, sender, date, snippet, body,
                    category, confidence, reasoning, summary,
                    requires_action, action_type, action_detail, deadline,
                    skipped, error
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?
                )
                """,
                (
                    run_id,
                    r.get("message_id", ""),
                    r.get("subject", ""),
                    r.get("sender", ""),
                    r.get("date", ""),
                    r.get("snippet", ""),
                    r.get("body", ""),
                    r.get("category", "other"),
                    r.get("confidence", 0.0),
                    r.get("reasoning", ""),
                    r.get("summary", ""),
                    1 if r.get("requires_action") else 0,
                    r.get("action_type", "none"),
                    r.get("action_detail", ""),
                    r.get("deadline"),
                    1 if r.get("skipped") else 0,
                    r.get("error"),
                ),
            )
            email_id = cursor.lastrowid

            # Insert reply draft if generated
            if r.get("reply_draft"):
                conn.execute(
                    """
                    INSERT INTO drafts (email_id, message_id, subject, recipient, body)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (email_id, r.get("message_id", ""), r.get("subject", ""), r.get("sender", ""), r.get("reply_draft", ""))
                )

            # Insert tasks if any
            if r.get("tasks"):
                for t in r["tasks"]:
                    conn.execute(
                        """
                        INSERT INTO tasks (email_id, title, description, priority, deadline)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (email_id, t.get("title", ""), t.get("description", ""), t.get("priority", "medium"), t.get("deadline"))
                    )

            # Insert calendar event if any
            if r.get("calendar_event"):
                evt = r["calendar_event"]
                conn.execute(
                    """
                    INSERT INTO calendar_events (email_id, title, description, start_time, end_time)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (email_id, evt.get("title", ""), evt.get("description", ""), evt.get("start_time", ""), evt.get("end_time"))
                )

    logger.info("Saved run #%d with %d emails.", run_id, len(results))
    return run_id


# ── Read operations ───────────────────────────────────────────────────────────

def get_latest_run() -> dict | None:
    """Return the most recent run metadata."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def get_emails_by_run(run_id: int) -> list[dict]:
    """Return all emails for a given run, sorted by category priority."""
    priority = "CASE category "\
               "WHEN 'important' THEN 1 "\
               "WHEN 'work' THEN 2 "\
               "WHEN 'jobs' THEN 3 "\
               "WHEN 'personal' THEN 4 "\
               "WHEN 'finance' THEN 5 "\
               "WHEN 'technology' THEN 6 "\
               "WHEN 'other' THEN 7 "\
               "WHEN 'ads' THEN 8 "\
               "ELSE 9 END"

    with get_db() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM emails
            WHERE run_id = ?
            ORDER BY {priority}, requires_action DESC
            """,
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_latest_emails() -> list[dict]:
    """Return all emails from the most recent run."""
    run = get_latest_run()
    if not run:
        return []
    return get_emails_by_run(run["id"])


def get_email_by_id(email_id: int) -> dict | None:
    """Return a single email by its database ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM emails WHERE id = ?", (email_id,)
        ).fetchone()
        return dict(row) if row else None


def get_stats() -> dict:
    """
    Return aggregate stats for the dashboard:
    - Category breakdown
    - Daily volume (last 7 days)
    - Action required rate
    - Top senders
    """
    with get_db() as conn:

        # Category breakdown (latest run only)
        run = get_latest_run()
        run_id = run["id"] if run else -1

        categories = conn.execute(
            """
            SELECT category, COUNT(*) as count
            FROM emails
            WHERE DATE(created_at, 'localtime') = DATE('now', 'localtime')
            GROUP BY category
            ORDER BY count DESC
            """
        ).fetchall()

        # Daily volume — last 7 days across all runs
        daily = conn.execute(
            """
            SELECT DATE(created_at) as day, COUNT(*) as count
            FROM emails
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY day
            ORDER BY day ASC
            """
        ).fetchall()

        # Action rate — latest run
        action_stats = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(requires_action) as action_count
            FROM emails
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        # Top 5 senders — latest run
        top_senders = conn.execute(
            """
            SELECT sender, COUNT(*) as count
            FROM emails
            WHERE run_id = ?
            GROUP BY sender
            ORDER BY count DESC
            LIMIT 5
            """,
            (run_id,),
        ).fetchall()

        # All runs summary
        runs_summary = conn.execute(
            """
            SELECT COUNT(*) as total_runs,
                   SUM(email_count) as total_emails
            FROM runs
            """
        ).fetchone()

        total = action_stats["total"] or 0
        action_count = action_stats["action_count"] or 0

        return {
            "latest_run": dict(run) if run else None,
            "category_breakdown": [dict(r) for r in categories],
            "daily_volume": [dict(r) for r in daily],
            "action_rate": round(action_count / total * 100, 1) if total else 0,
            "action_count": action_count,
            "total_emails": total,
            "top_senders": [dict(r) for r in top_senders],
            "total_runs": runs_summary["total_runs"] or 0,
            "all_time_emails": runs_summary["total_emails"] or 0,
        }


def get_all_runs() -> list[dict]:
    """Return all runs ordered by most recent first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT 30"
        ).fetchall()
        return [dict(r) for r in rows]


# ── Drafts operations ──────────────────────────────────────────────────────────

def get_pending_drafts() -> list[dict]:
    """Return all drafts with pending status."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT d.*, e.subject as email_subject, e.sender as email_sender, e.body as email_body
            FROM drafts d
            JOIN emails e ON d.email_id = e.id
            WHERE d.status = 'pending'
            ORDER BY d.id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


def get_draft_by_id(draft_id: int) -> dict | None:
    """Return a single draft by its ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM drafts WHERE id = ?", (draft_id,)
        ).fetchone()
        return dict(row) if row else None


def update_draft(draft_id: int, status: str, body: str | None = None) -> None:
    """Update draft status and optionally its body."""
    with get_db() as conn:
        if body is not None:
            conn.execute(
                "UPDATE drafts SET status = ?, body = ? WHERE id = ?",
                (status, body, draft_id)
            )
        else:
            conn.execute(
                "UPDATE drafts SET status = ? WHERE id = ?",
                (status, draft_id)
            )


# ── Tasks operations ───────────────────────────────────────────────────────────

def get_tasks(status: str | None = None) -> list[dict]:
    """Return all tasks, optionally filtered by status."""
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY id DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def update_task_status(task_id: int, status: str) -> None:
    """Update a task's status (e.g. 'todo' or 'done')."""
    with get_db() as conn:
        conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id)
        )


# ── Calendar operations ───────────────────────────────────────────────────────

def get_calendar_events(status: str | None = None) -> list[dict]:
    """Return all calendar events, optionally filtered by status."""
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM calendar_events WHERE status = ? ORDER BY start_time ASC", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM calendar_events ORDER BY start_time ASC"
            ).fetchall()
        return [dict(r) for r in rows]


def get_calendar_event_by_id(event_id: int) -> dict | None:
    """Return a single calendar event by its ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM calendar_events WHERE id = ?", (event_id,)
        ).fetchone()
        return dict(row) if row else None


def update_calendar_event(event_id_db: int, status: str, event_id_google: str | None = None) -> None:
    """Update event status and optionally store Google Calendar event ID."""
    with get_db() as conn:
        if event_id_google:
            conn.execute(
                "UPDATE calendar_events SET status = ?, event_id = ? WHERE id = ?",
                (status, event_id_google, event_id_db)
            )
        else:
            conn.execute(
                "UPDATE calendar_events SET status = ? WHERE id = ?",
                (status, event_id_db)
            )