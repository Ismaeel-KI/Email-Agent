import logging
from app.schemas import EmailState
from app.llms import get_openrouter
from app.prompts import SUMMARIZER_SYSTEM_PROMPT, SUMMARIZER_USER_PROMPT
from app.tools.base import call_llm_json

logger = logging.getLogger("email-agent.tools.summarizer")


def summarize(state: EmailState) -> EmailState:
    """
    Summarizer node — generates a 1-2 sentence summary of the email.
    Uses OpenRouter (Gemma) for cost efficiency.
    Updates state with: summary.
    """
    logger.info("Summarizing email: %s", state["subject"])

    try:
        user_prompt = SUMMARIZER_USER_PROMPT.format(
            sender=state["sender"],
            subject=state["subject"],
            body=state["body"] or state["snippet"],
        )
        result = call_llm_json(
            llm=get_openrouter(),
            system_prompt=SUMMARIZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        summary = result.get("summary", "").strip()
        logger.info("Summary generated for: %s", state["subject"])

        return {
            **state,
            "summary": summary,
        }

    except Exception as e:
        logger.error("Summarizer failed for '%s': %s", state["subject"], e)
        return {
            **state,
            "summary": state.get("snippet", ""),   # fall back to Gmail snippet
            "error": str(e),
        }