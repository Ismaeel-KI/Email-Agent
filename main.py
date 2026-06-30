import sys
from datetime import datetime, timezone
from app.config import settings, logger
from app.gmail import GmailClient
from app.agents import EmailAgent
from app.utils import StateManager, format_digest
from app.database import init_db, save_run


def main() -> None:
    logger.info("Initializing Email Agent...")

    # ── Validate env vars ─────────────────────────────────────────────────────
    try:
        settings.validate()
    except EnvironmentError as e:
        logger.error(str(e))
        sys.exit(1)

    # ── Check credentials.json exists ─────────────────────────────────────────
    if not settings.CREDENTIALS_FILE.exists():
        logger.error(
            f"credentials.json not found at {settings.CREDENTIALS_FILE}.\n"
            "Download it from Google Cloud Console and place it in credentials/."
        )
        sys.exit(1)

    # ── Initialize database ───────────────────────────────────────────────────
    init_db()

    # ── Load last_run from state.json ─────────────────────────────────────────
    state = StateManager()
    last_run = state.get_last_run()

    if last_run:
        logger.info("Last run: %s", last_run.isoformat())
    else:
        logger.info("First run — fetching last 24 hours of emails.")

    # ── Fetch emails since last run ───────────────────────────────────────────
    logger.info("Connecting to Gmail...")
    client = GmailClient()
    emails = client.fetch_emails_since(since=last_run)

    if not emails:
        logger.info("No new emails since last run. Exiting.")
        state.save_last_run()
        return

    logger.info("Fetched %d email(s). Starting pipeline...", len(emails))

    # ── Run LangGraph pipeline ────────────────────────────────────────────────
    run_time = datetime.now(timezone.utc)
    agent = EmailAgent()
    results = agent.run(emails)

    # ── Save results to database ──────────────────────────────────────────────
    run_id = save_run(results, run_at=run_time)
    logger.info("Results saved to database (run #%d).", run_id)

    # ── Mark emails as read in Gmail ──────────────────────────────────────────
    processed_ids = [r["message_id"] for r in results if r.get("message_id")]
    if processed_ids:
        try:
            client.mark_as_read(processed_ids)
        except Exception as e:
            logger.error("Failed to mark emails as read in Gmail: %s", e)

    # ── Print rich CLI digest ─────────────────────────────────────────────────
    format_digest(results, run_time=run_time)

    # ── Save last_run timestamp ───────────────────────────────────────────────
    state.save_last_run(run_time)
    logger.info("Done.")


if __name__ == "__main__":
    main()