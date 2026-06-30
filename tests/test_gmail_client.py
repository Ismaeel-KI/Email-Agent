"""
Tests for app/gmail/client.py
Mocks the Gmail API — no real network calls.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from app.gmail.client import GmailClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_raw_message(
    subject="Test Subject",
    sender="sender@example.com",
    date="Sat, 28 Jun 2026 10:00:00 +0000",
    body_data: str | None = None,
) -> dict:
    """Build a fake Gmail API message response."""
    import base64
    body_text = "This is a test email body."
    encoded = base64.urlsafe_b64encode(body_text.encode()).decode()
    data = body_data or encoded

    return {
        "id": "msg_test_001",
        "snippet": "This is a test email body.",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": sender},
                {"name": "Date", "value": date},
            ],
            "body": {"data": data},
            "parts": [],
        },
    }


@pytest.fixture
def mock_gmail_client():
    """GmailClient with mocked Gmail API service."""
    with patch("app.gmail.client.get_credentials") as mock_creds, \
         patch("app.gmail.client.build") as mock_build:

        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        client = GmailClient()
        client._service = mock_service
        return client, mock_service


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestGmailClientParsing:

    def test_parse_message_extracts_headers(self, mock_gmail_client):
        client, _ = mock_gmail_client
        raw = make_raw_message(
            subject="Hello World",
            sender="alice@example.com",
        )
        result = client._parse_message(raw)

        assert result is not None
        assert result["subject"] == "Hello World"
        assert result["sender"] == "alice@example.com"
        assert result["message_id"] == "msg_test_001"

    def test_parse_message_decodes_body(self, mock_gmail_client):
        client, _ = mock_gmail_client
        raw = make_raw_message()
        result = client._parse_message(raw)

        assert result is not None
        assert "test email body" in result["body"]

    def test_parse_message_missing_subject(self, mock_gmail_client):
        client, _ = mock_gmail_client
        raw = make_raw_message()
        # Remove subject header
        raw["payload"]["headers"] = [
            h for h in raw["payload"]["headers"]
            if h["name"] != "Subject"
        ]
        result = client._parse_message(raw)

        assert result is not None
        assert result["subject"] == "(no subject)"

    def test_body_truncated_at_2000_chars(self, mock_gmail_client):
        import base64
        client, _ = mock_gmail_client
        long_body = "x" * 3000
        encoded = base64.urlsafe_b64encode(long_body.encode()).decode()
        raw = make_raw_message(body_data=encoded)
        result = client._parse_message(raw)

        assert result is not None
        assert len(result["body"]) <= 2020  # 2000 + truncation marker
        assert "[truncated]" in result["body"]

    def test_base64_decode_handles_padding(self, mock_gmail_client):
        client, _ = mock_gmail_client
        # Test with various padding lengths
        import base64
        text = "Hello, World!"
        encoded = base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")
        result = client._decode_base64(encoded)
        assert result == text


class TestGmailClientFetch:

    def test_fetch_returns_empty_when_no_messages(self, mock_gmail_client):
        client, mock_service = mock_gmail_client
        mock_service.users().messages().list().execute.return_value = {
            "messages": []
        }
        since = datetime(2026, 6, 28, tzinfo=timezone.utc)
        result = client.fetch_emails_since(since=since)
        assert result == []

    def test_build_query_format(self, mock_gmail_client):
        client, _ = mock_gmail_client
        since = datetime(2026, 6, 28, 0, 0, 0, tzinfo=timezone.utc)
        query = client._build_query(since)
        assert "after:" in query
        assert "-from:me" in query

    def test_fetch_uses_default_max_results(self, mock_gmail_client):
        client, mock_service = mock_gmail_client
        mock_service.users().messages().list().execute.return_value = {"messages": []}

        since = datetime(2026, 6, 28, tzinfo=timezone.utc)
        client.fetch_emails_since(since=since)

        mock_service.users().messages().list.assert_called_with(
            userId="me",
            q=client._build_query(since),
            maxResults=20,
        )

    def test_mark_as_read_calls_batch_modify(self, mock_gmail_client):
        client, mock_service = mock_gmail_client
        mock_service.users().messages().batchModify().execute.return_value = {}

        client.mark_as_read(["msg_1", "msg_2"])

        mock_service.users().messages().batchModify.assert_called_with(
            userId="me",
            body={
                "ids": ["msg_1", "msg_2"],
                "removeLabelIds": ["UNREAD"]
            }
        )