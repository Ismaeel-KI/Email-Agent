import logging
from app.schemas import EmailState
from app.llms import get_gemini
from app.prompts import REPLY_GENERATOR_SYSTEM_PROMPT, REPLY_GENERATOR_USER_PROMPT
from app.tools.base import call_llm_json

logger = logging.getLogger("email-agent.tools.reply_generator")


def generate_reply_draft(state: EmailState) -> EmailState:
    """
    Reply Generator node — drafts a reply for emails requiring action.
    """
    if state.get("skipped") or not state.get("requires_action"):
        return state

    logger.info("Generating reply draft for email: %s", state["subject"])

    try:
        user_prompt = REPLY_GENERATOR_USER_PROMPT.format(
            sender=state["sender"],
            subject=state["subject"],
            body=state["body"] or state["snippet"],
            summary=state.get("summary", ""),
            action_detail=state.get("action_detail", ""),
        )
        result = call_llm_json(
            llm=get_gemini(),
            system_prompt=REPLY_GENERATOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        reply_draft = result.get("reply_draft", "").strip()

        return {
            **state,
            "reply_draft": reply_draft,
        }

    except Exception as e:
        logger.error("Reply generator failed for '%s': %s", state["subject"], e)
        return {
            **state,
            "reply_draft": None,
            "error": str(e) if state.get("error") is None else f"{state['error']}; {e}",
        }
