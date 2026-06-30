import logging
from langgraph.graph import StateGraph, END
from app.schemas import EmailState
from app.tools import (
    categorize, summarize, detect_action,
    generate_reply_draft, extract_tasks, extract_calendar_events
)
from langgraph.graph.state import CompiledStateGraph


logger = logging.getLogger("email-agent.graph")


def route_after_categorize(state: EmailState) -> str:
    """
    Conditional routing after categorizer node.
    Ads are skipped directly to END — no summarization or action detection needed.
    Everything else goes to summarizer.
    """
    if state.get("skipped") or state.get("category") == "ads":
        logger.info("Email is an ad — skipping summarizer and action detector.")
        return "skip"
    return "summarize"


def build_email_graph() -> CompiledStateGraph:
    """
    Build and compile the LangGraph email processing pipeline.

    Flow:
        categorize
            ├── (ads)  → END
            └── (else) → summarize → detect_action → generate_reply_draft → extract_tasks → extract_calendar_events → END
    """
    graph = StateGraph(EmailState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("categorize", categorize)
    graph.add_node("summarize", summarize)
    graph.add_node("detect_action", detect_action)
    graph.add_node("generate_reply_draft", generate_reply_draft)
    graph.add_node("extract_tasks", extract_tasks)
    graph.add_node("extract_calendar_events", extract_calendar_events)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("categorize")

    # ── Conditional routing after categorize ──────────────────────────────────
    graph.add_conditional_edges(
        "categorize",
        route_after_categorize,
        {
            "skip": END,        # ads → stop here
            "summarize": "summarize",
        },
    )

    # ── Linear edges for remaining nodes ──────────────────────────────────────
    graph.add_edge("summarize", "detect_action")
    graph.add_edge("detect_action", "generate_reply_draft")
    graph.add_edge("generate_reply_draft", "extract_tasks")
    graph.add_edge("extract_tasks", "extract_calendar_events")
    graph.add_edge("extract_calendar_events", END)

    return graph.compile()


# Compiled graph — imported by the agent runner
email_graph = build_email_graph()