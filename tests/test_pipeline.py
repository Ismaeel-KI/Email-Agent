"""
End-to-end pipeline tests for the LangGraph email processing graph.
Mocks all LLM calls — tests graph routing and state flow.
"""
import json
from typing import cast
import pytest
from unittest.mock import MagicMock, patch
from app.schemas import EmailInput, EmailState


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_state(**overrides) -> EmailState:
    base: EmailState = {
        "message_id": "msg_001",
        "subject": "Test Subject",
        "sender": "sender@example.com",
        "date": "Sat, 28 Jun 2026 10:00:00 +0000",
        "snippet": "Test snippet.",
        "body": "Test body content.",
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
    mock_response = MagicMock()
    mock_response.content = json.dumps(content)
    return mock_response


# ── Pipeline routing tests ────────────────────────────────────────────────────

class TestEmailGraphRouting:

    @patch("app.tools.calendar_extractor.get_gemini")
    @patch("app.tools.task_extractor.get_gemini")
    @patch("app.tools.reply_generator.get_gemini")
    @patch("app.tools.detect_action.get_openrouter")
    @patch("app.tools.summarize.get_openrouter")
    @patch("app.tools.categorize.get_openrouter")
    def test_non_ad_goes_through_full_pipeline(
        self, mock_cat_llm, mock_sum_llm, mock_act_llm, mock_rep_llm, mock_tsk_llm, mock_cal_llm
    ):
        from app.graphs.email_graph import email_graph

        mock_cat_llm.return_value.invoke.return_value = mock_llm_response({
            "category": "jobs", "confidence": 0.99, "reasoning": "Job email."
        })
        mock_sum_llm.return_value.invoke.return_value = mock_llm_response({
            "summary": "Recruiter reached out about a Python role."
        })
        mock_act_llm.return_value.invoke.return_value = mock_llm_response({
            "requires_action": True,
            "action_type": "reply",
            "action_detail": "Reply to confirm interest.",
            "deadline": "Friday",
        })
        mock_rep_llm.return_value.invoke.return_value = mock_llm_response({
            "reply_draft": "Hi, thanks for reaching out. I am interested."
        })
        mock_tsk_llm.return_value.invoke.return_value = mock_llm_response({
            "tasks": [{"title": "Submit Resume", "description": "Send PDF resume.", "priority": "high", "deadline": "2026-07-02"}]
        })
        mock_cal_llm.return_value.invoke.return_value = mock_llm_response({
            "calendar_event": {"title": "Interview", "description": "TechCorp Interview", "start_time": "2026-07-03T10:00:00"}
        })

        state = make_state(subject="Senior Python Developer Role")
        result = email_graph.invoke(state)

        # All nodes should have run
        assert result["category"] == "jobs"
        assert result["summary"] == "Recruiter reached out about a Python role."
        assert result["requires_action"] is True
        assert result["action_type"] == "reply"
        assert result["skipped"] is False
        assert result["reply_draft"] == "Hi, thanks for reaching out. I am interested."
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "Submit Resume"
        assert result["calendar_event"]["title"] == "Interview"

    @patch("app.tools.categorize.get_openrouter")
    def test_ad_skips_summarizer_and_action_detector(self, mock_cat_llm):
        from app.graphs.email_graph import email_graph

        mock_cat_llm.return_value.invoke.return_value = mock_llm_response({
            "category": "ads", "confidence": 0.95, "reasoning": "Promotional email."
        })

        state = make_state(subject="50% Off Flash Sale!")
        result = email_graph.invoke(state)

        # Only categorizer ran — summary and action should be None
        assert result["category"] == "ads"
        assert result["skipped"] is True
        assert result["summary"] is None
        assert result["requires_action"] is None

    @patch("app.tools.calendar_extractor.get_gemini")
    @patch("app.tools.task_extractor.get_gemini")
    @patch("app.tools.reply_generator.get_gemini")
    @patch("app.tools.detect_action.get_openrouter")
    @patch("app.tools.summarize.get_openrouter")
    @patch("app.tools.categorize.get_openrouter")
    def test_state_fields_preserved_through_pipeline(
        self, mock_cat_llm, mock_sum_llm, mock_act_llm, mock_rep_llm, mock_tsk_llm, mock_cal_llm
    ):
        from app.graphs.email_graph import email_graph

        mock_cat_llm.return_value.invoke.return_value = mock_llm_response({
            "category": "important", "confidence": 0.98, "reasoning": "Security alert."
        })
        mock_sum_llm.return_value.invoke.return_value = mock_llm_response({
            "summary": "Google detected a new sign-in to your account."
        })
        mock_act_llm.return_value.invoke.return_value = mock_llm_response({
            "requires_action": True,
            "action_type": "review",
            "action_detail": "Review account activity.",
            "deadline": None,
        })
        mock_rep_llm.return_value.invoke.return_value = mock_llm_response({
            "reply_draft": "Reviewing."
        })
        mock_tsk_llm.return_value.invoke.return_value = mock_llm_response({
            "tasks": []
        })
        mock_cal_llm.return_value.invoke.return_value = mock_llm_response({
            "calendar_event": None
        })

        state = make_state(
            subject="Security Alert",
            sender="security@google.com",
            body="A new sign-in was detected.",
        )
        result = email_graph.invoke(state)

        # Original fields preserved
        assert result["message_id"] == "msg_001"
        assert result["sender"] == "security@google.com"
        # Enriched fields set correctly
        assert result["category"] == "important"
        assert result["requires_action"] is True
        assert result["deadline"] is None


# ── Agent runner tests ────────────────────────────────────────────────────────

class TestEmailAgent:

    @patch("app.tools.detect_action.get_openrouter")
    @patch("app.tools.summarize.get_openrouter")
    @patch("app.tools.categorize.get_openrouter")
    def test_agent_processes_batch(
        self, mock_cat_llm, mock_sum_llm, mock_act_llm
    ):
        from app.agents.email_agent import EmailAgent

        mock_cat_llm.return_value.invoke.return_value = mock_llm_response({
            "category": "jobs", "confidence": 0.9, "reasoning": "Job email."
        })
        mock_sum_llm.return_value.invoke.return_value = mock_llm_response({
            "summary": "Job opportunity at TechCorp."
        })
        mock_act_llm.return_value.invoke.return_value = mock_llm_response({
            "requires_action": False,
            "action_type": "none",
            "action_detail": "",
            "deadline": None,
        })

        emails: list[EmailInput] = [
            {
                "message_id": f"msg_00{i}",
                "subject": f"Job {i}",
                "sender": "recruiter@example.com",
                "date": "Sat, 28 Jun 2026 10:00:00 +0000",
                "snippet": "Job opportunity.",
                "body": "You have a new job opportunity.",
            }
            for i in range(3)
        ]

        agent = EmailAgent()
        results = agent.run(emails)

        assert len(results) == 3
        assert all(r["category"] == "jobs" for r in results)

    def test_agent_returns_empty_for_no_emails(self):
        from app.agents.email_agent import EmailAgent
        agent = EmailAgent()
        results = agent.run([])
        assert results == []