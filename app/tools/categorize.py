import logging
from app.schemas import EmailState
from app.llms import get_openrouter
from app.prompts import CATEGORIZER_SYSTEM_PROMPT, CATEGORIZER_USER_PROMPT
from app.tools.base import call_llm_json

logger = logging.getLogger("email-agent.tools.categorizer")


def categorize(state: EmailState) -> EmailState:
    """
    Categorizer node — classifies the email into a category.
    Uses OpenRouter (Gemma) for cost efficiency.
    Updates state with: category, confidence, reasoning.
    """
    logger.info("Categorizing email: %s", state["subject"])

    try:
        user_prompt = CATEGORIZER_USER_PROMPT.format(
            sender=state["sender"],
            subject=state["subject"],
            body=state["body"] or state["snippet"],
        )
        result = call_llm_json(
            llm=get_openrouter(),
            system_prompt=CATEGORIZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        category = result.get("category", "other").lower().strip()
        logger.info(
            "Categorized as '%s' (confidence: %s)",
            category,
            result.get("confidence"),
        )

        return {
            **state,
            "category": category,
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", ""),
            "skipped": category == "ads",
        }

    except Exception as e:
        logger.error("Categorizer failed for '%s': %s", state["subject"], e)
        return {
            **state,
            "category": "other",
            "confidence": 0.0,
            "reasoning": "",
            "skipped": False,
            "error": str(e),
        }