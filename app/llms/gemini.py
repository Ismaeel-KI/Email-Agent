import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

logger = logging.getLogger("email-agent.llms")

_gemini_instance: ChatGoogleGenerativeAI | None = None


def get_gemini() -> ChatGoogleGenerativeAI:
    """
    Return a cached Gemini LLM instance.
    Used by the coordinator node to generate the final digest.
    """
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
        )
        logger.debug("Gemini LLM initialized: %s", settings.GEMINI_MODEL)
    return _gemini_instance