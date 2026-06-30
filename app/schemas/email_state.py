from typing import Optional
from typing_extensions import TypedDict


class EmailInput(TypedDict):
    """Raw email fetched from Gmail API."""
    message_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body: str


class CategoryResult(TypedDict):
    """Output from the categorizer node."""
    category: str
    confidence: float
    reasoning: str


class SummaryResult(TypedDict):
    """Output from the summarizer node."""
    summary: str


class ActionResult(TypedDict):
    """Output from the action detector node."""
    requires_action: bool
    action_type: str        # reply | review | deadline | click | none
    action_detail: str
    deadline: Optional[str]


class EmailState(TypedDict):
    """
    Full state object that flows through the LangGraph pipeline.
    Starts with raw email fields, gets enriched by each node.
    """
    # ── Input (from Gmail) ────────────────────────────────────────────────────
    message_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body: str

    # ── Enriched by nodes ─────────────────────────────────────────────────────
    category: Optional[str]
    confidence: Optional[float]
    reasoning: Optional[str]
    summary: Optional[str]
    requires_action: Optional[bool]
    action_type: Optional[str]
    action_detail: Optional[str]
    deadline: Optional[str]

    # ── Pipeline metadata ─────────────────────────────────────────────────────
    error: Optional[str]        # set if a node fails
    skipped: Optional[bool]     # set to True for ads (skip summarizer/action)

    # ── Phase 2 extensions ────────────────────────────────────────────────────
    reply_draft: Optional[str]
    tasks: Optional[list[dict]]
    calendar_event: Optional[dict]