import logging
from app.schemas import EmailState
from app.llms import get_gemini
from app.prompts import TASK_EXTRACTOR_SYSTEM_PROMPT, TASK_EXTRACTOR_USER_PROMPT
from app.tools.base import call_llm_json

logger = logging.getLogger("email-agent.tools.task_extractor")


def extract_tasks(state: EmailState) -> EmailState:
    """
    Task Extractor node — parses emails that require action and extracts tasks.
    """
    if state.get("skipped") or not state.get("requires_action"):
        return state

    logger.info("Extracting tasks from email: %s", state["subject"])

    try:
        user_prompt = TASK_EXTRACTOR_USER_PROMPT.format(
            sender=state["sender"],
            subject=state["subject"],
            body=state["body"] or state["snippet"],
            summary=state.get("summary", ""),
            action_detail=state.get("action_detail", ""),
        )
        result = call_llm_json(
            llm=get_gemini(),
            system_prompt=TASK_EXTRACTOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        tasks = result.get("tasks", [])

        return {
            **state,
            "tasks": tasks,
        }

    except Exception as e:
        logger.error("Task extractor failed for '%s': %s", state["subject"], e)
        return {
            **state,
            "tasks": [],
            "error": str(e) if state.get("error") is None else f"{state['error']}; {e}",
        }
