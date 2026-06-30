import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger("email-agent.tools")


def call_llm_json(
    llm: BaseChatModel,
    system_prompt: str,
    user_prompt: str,
) -> dict:
    """
    Call an LLM with a system + user prompt and parse the JSON response.
    Handles markdown code fences and both string/list response types.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)

    # Handle both string and list content types
    content = response.content
    if isinstance(content, list):
        raw = " ".join(
            block["text"] if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    else:
        raw = str(content).strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())