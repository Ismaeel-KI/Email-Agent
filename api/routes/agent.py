import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from api.models import AgentStatusResponse, AgentRunResponse
from app.database import save_run, get_latest_run
from app.utils import StateManager

router = APIRouter()
logger = logging.getLogger("email-agent.api.agent")

_agent_running: bool = False


async def _run_agent_task() -> tuple[int, int]:
    """Run the full agent pipeline. Returns (run_id, email_count)."""
    global _agent_running
    from app.gmail import GmailClient
    from app.agents import EmailAgent

    _agent_running = True
    try:
        state = StateManager()
        last_run = state.get_last_run()

        client = GmailClient()
        emails = await asyncio.to_thread(client.fetch_emails_since, last_run)

        if not emails:
            logger.info("No new emails found.")
            state.save_last_run()
            return -1, 0

        run_time = datetime.now(timezone.utc)
        agent = EmailAgent()
        results = await asyncio.to_thread(agent.run, emails)

        run_id = save_run(results, run_at=run_time)
        state.save_last_run(run_time)

        # ── Mark emails as read in Gmail ──────────────────────────────────────────
        processed_ids = [r["message_id"] for r in results if r.get("message_id")]
        if processed_ids:
            try:
                await asyncio.to_thread(client.mark_as_read, processed_ids)
            except Exception as e:
                logger.error("Failed to mark emails as read in Gmail: %s", e)

        logger.info("Manual run complete. Run #%d, %d emails.", run_id, len(results))
        return run_id, len(results)

    finally:
        _agent_running = False


@router.get("/status", response_model=AgentStatusResponse)
async def agent_status():
    """Return current agent status and last run info."""
    run = get_latest_run()
    return AgentStatusResponse(
        is_running=_agent_running,
        last_run=run["run_at"] if run else None,
        last_run_email_count=run["email_count"] if run else None,
    )


@router.post("/run", response_model=AgentRunResponse)
async def run_agent():
    """Manually trigger the email agent pipeline."""
    global _agent_running

    if _agent_running:
        raise HTTPException(
            status_code=409,
            detail="Agent is already running. Wait for it to finish."
        )

    try:
        run_id, email_count = await _run_agent_task()

        if run_id == -1:
            return AgentRunResponse(
                success=True,
                message="No new emails found.",
                email_count=0,
            )

        return AgentRunResponse(
            success=True,
            message="Agent completed successfully.",
            run_id=run_id,
            email_count=email_count,
        )

    except Exception as e:
        logger.error("Agent run failed: %s", e)
        _agent_running = False
        raise HTTPException(status_code=500, detail=str(e))