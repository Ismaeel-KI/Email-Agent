import logging
from langchain_openai import ChatOpenAI
from app.config import settings

logger = logging.getLogger("email-agent.llms")

_openrouter_instance: ChatOpenAI | None = None


def get_openrouter() -> ChatOpenAI:
    """
    Return a cached OpenRouter LLM instance.
    Used by categorizer, summarizer, and action detector nodes.
    """
    global _openrouter_instance
    if _openrouter_instance is None:
        _openrouter_instance = ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            temperature=0.1,    # low temp for consistent structured output
        )
        logger.debug("OpenRouter LLM initialized: %s", settings.OPENROUTER_MODEL)
    return _openrouter_instance