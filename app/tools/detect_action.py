import logging
from app.schemas import EmailState
from app.llms import get_openrouter
from app.prompts import ACTION_DETECTOR_SYSTEM_PROMPT, ACTION_DETECTOR_USER_PROMPT
from app.tools.base import call_llm_json

logger = logging.getLogger("email-agent.tools.action_detector")


def detect_action(state: EmailState) -> EmailState:
    """
    Action detector node — determines if the email needs a reply, review,
    or has a deadline. Uses OpenRouter (Gemma).
    Updates state with: requires_action, action_type, action_detail, deadline.
    """
    logger.info("Detecting actions for email: %s", state["subject"])

    try:
        user_prompt = ACTION_DETECTOR_USER_PROMPT.format(
            sender=state["sender"],
            subject=state["subject"],
            body=state["body"] or state["snippet"],
        )
        result = call_llm_json(
            llm=get_openrouter(),
            system_prompt=ACTION_DETECTOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        requires_action = result.get("requires_action", False)
        logger.info(
            "Action detected: %s (%s)",
            result.get("action_type", "none"),
            "required" if requires_action else "not required",
        )

        return {
            **state,
            "requires_action": requires_action,
            "action_type": result.get("action_type", "none"),
            "action_detail": result.get("action_detail", ""),
            "deadline": result.get("deadline", None),
        }

    except Exception as e:
        logger.error("Action detector failed for '%s': %s", state["subject"], e)
        return {
            **state,
            "requires_action": False,
            "action_type": "none",
            "action_detail": "",
            "deadline": None,
            "error": str(e),
        }