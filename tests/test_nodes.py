"""
Tests for app/tools/ nodes.
Mocks the LLM calls — no real API calls.
"""
import json
from typing import cast
import pytest
from unittest.mock import MagicMock, patch
from app.schemas import EmailState


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_state(**overrides) -> EmailState:
    """Build a minimal EmailState for testing."""
    base: EmailState = {
        "message_id": "msg_001",
        "subject": "Test Subject",
        "sender": "sender@example.com",
        "date": "Sat, 28 Jun 2026 10:00:00 +0000",
        "snippet": "Test snippet.",
        "body": "This is the email body for testing purposes.",
        "category": None,
        "confidence": None,
        "reasoning": None,
        "summary": None,
        "requires_action": None,
        "action_type": None,
        "action_detail": None,
        "deadline": None,
        "error": None,
        "skipped": False,
    }
    return cast(EmailState, {**base, **overrides})


def mock_llm_response(content: dict) -> MagicMock:
    """Return a mock LLM response with JSON content."""
    mock_response = MagicMock()
    mock_response.content = json.dumps(content)
    return mock_response


# ── Categorizer tests ─────────────────────────────────────────────────────────

class TestCategorizerNode:

    @patch("app.tools.categorize.get_openrouter")
    def test_categorizes_job_email(self, mock_get_llm):
        from app.tools.categorize import categorize

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response({
            "category": "jobs",
            "confidence": 0.99,
            "reasoning": "Recruiter outreach for a developer role.",
        })
        mock_get_llm.return_value = mock_llm

        state = make_state(subject="Senior Python Developer Role")
        result = categorize(state)

        assert result["category"] == "jobs"
        assert result["confidence"] == 0.99
        assert result["skipped"] is False

    @patch("app.tools.categorize.get_openrouter")
    def test_ads_sets_skipped_true(self, mock_get_llm):
        from app.tools.categorize import categorize

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response({
            "category": "ads",
            "confidence": 0.95,
            "reasoning": "Promotional email with discount offers.",
        })
        mock_get_llm.return_value = mock_llm

        state = make_state(subject="50% Off Flash Sale!")
        result = categorize(state)

        assert result["category"] == "ads"
        assert result["skipped"] is True

    @patch("app.tools.categorize.get_openrouter")
    def test_categorizer_handles_llm_failure(self, mock_get_llm):
        from app.tools.categorize import categorize

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("LLM timeout")
        mock_get_llm.return_value = mock_llm

        state = make_state()
        result = categorize(state)

        # Should fall back gracefully
        assert result["category"] == "other"
        assert result["error"] is not None
        assert result["skipped"] is False


# ── Summarizer tests ──────────────────────────────────────────────────────────

class TestSummarizerNode:

    @patch("app.tools.summarize.get_openrouter")
    def test_generates_summary(self, mock_get_llm):
        from app.tools.summarize import summarize

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response({
            "summary": "TechCorp recruiter reached out about a Python role offering ₹30LPA.",
        })
        mock_get_llm.return_value = mock_llm

        state = make_state()
        result = summarize(state)

        assert result["summary"] == "TechCorp recruiter reached out about a Python role offering ₹30LPA."

    @patch("app.tools.summarize.get_openrouter")
    def test_summarizer_falls_back_to_snippet(self, mock_get_llm):
        from app.tools.summarize import summarize

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("LLM error")
        mock_get_llm.return_value = mock_llm

        state = make_state(snippet="This is the fallback snippet.")
        result = summarize(state)

        # Falls back to snippet on error
        assert result["summary"] == "This is the fallback snippet."
        assert result["error"] is not None


# ── Action detector tests ─────────────────────────────────────────────────────

class TestActionDetectorNode:

    @patch("app.tools.detect_action.get_openrouter")
    def test_detects_reply_action(self, mock_get_llm):
        from app.tools.detect_action import detect_action

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response({
            "requires_action": True,
            "action_type": "reply",
            "action_detail": "Recruiter is asking for a resume and confirmation.",
            "deadline": "by Friday",
        })
        mock_get_llm.return_value = mock_llm

        state = make_state()
        result = detect_action(state)

        assert result["requires_action"] is True
        assert result["action_type"] == "reply"
        assert result["deadline"] == "by Friday"

    @patch("app.tools.detect_action.get_openrouter")
    def test_detects_no_action(self, mock_get_llm):
        from app.tools.detect_action import detect_action

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response({
            "requires_action": False,
            "action_type": "none",
            "action_detail": "",
            "deadline": None,
        })
        mock_get_llm.return_value = mock_llm

        state = make_state()
        result = detect_action(state)

        assert result["requires_action"] is False
        assert result["action_type"] == "none"
        assert result["deadline"] is None

    @patch("app.tools.detect_action.get_openrouter")
    def test_action_detector_handles_failure(self, mock_get_llm):
        from app.tools.detect_action import detect_action

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API error")
        mock_get_llm.return_value = mock_llm

        state = make_state()
        result = detect_action(state)

        assert result["requires_action"] is False
        assert result["action_type"] == "none"
        assert result["error"] is not None


# ── Reply Generator tests ─────────────────────────────────────────────────────

class TestReplyGeneratorNode:

    @patch("app.tools.reply_generator.get_gemini")
    def test_generates_reply_draft(self, mock_get_llm):
        from app.tools.reply_generator import generate_reply_draft

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response({
            "reply_draft": "Hi, thanks for reaching out. I am interested.",
        })
        mock_get_llm.return_value = mock_llm

        state = make_state(requires_action=True, action_type="reply")
        result = generate_reply_draft(state)

        assert result["reply_draft"] == "Hi, thanks for reaching out. I am interested."

    def test_skips_reply_draft_when_no_action_needed(self):
        from app.tools.reply_generator import generate_reply_draft

        state = make_state(requires_action=False)
        result = generate_reply_draft(state)

        assert result.get("reply_draft") is None


# ── Task Extractor tests ──────────────────────────────────────────────────────

class TestTaskExtractorNode:

    @patch("app.tools.task_extractor.get_gemini")
    def test_extracts_tasks(self, mock_get_llm):
        from app.tools.task_extractor import extract_tasks

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response({
            "tasks": [
                {"title": "Submit Resume", "description": "Send PDF resume.", "priority": "high", "deadline": "2026-07-02"}
            ]
        })
        mock_get_llm.return_value = mock_llm

        state = make_state(requires_action=True)
        result = extract_tasks(state)

        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "Submit Resume"
        assert result["tasks"][0]["priority"] == "high"


# ── Calendar Extractor tests ──────────────────────────────────────────────────

class TestCalendarExtractorNode:

    @patch("app.tools.calendar_extractor.get_gemini")
    def test_extracts_calendar_event(self, mock_get_llm):
        from app.tools.calendar_extractor import extract_calendar_events

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response({
            "calendar_event": {
                "title": "Interview with TechCorp",
                "description": "Google Meet link in thread.",
                "start_time": "2026-07-03T10:00:00",
                "end_time": "2026-07-03T11:00:00",
            }
        })
        mock_get_llm.return_value = mock_llm

        state = make_state(requires_action=True)
        result = extract_calendar_events(state)

        assert result["calendar_event"] is not None
        assert result["calendar_event"]["title"] == "Interview with TechCorp"
        assert result["calendar_event"]["start_time"] == "2026-07-03T10:00:00"