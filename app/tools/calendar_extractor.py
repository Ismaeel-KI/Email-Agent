import logging
from app.schemas import EmailState
from app.llms import get_gemini
from app.prompts import CALENDAR_EXTRACTOR_SYSTEM_PROMPT, CALENDAR_EXTRACTOR_USER_PROMPT
from app.tools.base import call_llm_json

logger = logging.getLogger("email-agent.tools.calendar_extractor")


def extract_calendar_events(state: EmailState) -> EmailState:
    """
    Calendar Extractor node — extracts calendar events from emails.
    """
    if state.get("skipped") or not state.get("requires_action"):
        return state

    logger.info("Extracting calendar events from email: %s", state["subject"])

    try:
        user_prompt = CALENDAR_EXTRACTOR_USER_PROMPT.format(
            sender=state["sender"],
            subject=state["subject"],
            body=state["body"] or state["snippet"],
            summary=state.get("summary", ""),
            action_detail=state.get("action_detail", ""),
        )
        result = call_llm_json(
            llm=get_gemini(),
            system_prompt=CALENDAR_EXTRACTOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        calendar_event = result.get("calendar_event")
        # Check if the keys are actually present and not null
        if calendar_event and (not calendar_event.get("title") or not calendar_event.get("start_time")):
            calendar_event = None

        return {
            **state,
            "calendar_event": calendar_event,
        }

    except Exception as e:
        logger.error("Calendar extractor failed for '%s': %s", state["subject"], e)
        return {
            **state,
            "calendar_event": None,
            "error": str(e) if state.get("error") is None else f"{state['error']}; {e}",
        }
