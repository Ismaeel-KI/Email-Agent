import base64
import logging
from datetime import datetime, timezone, timedelta
from typing import TypedDict

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.gmail.auth import get_credentials

logger = logging.getLogger("email-agent.client")


class EmailDict(TypedDict):
    message_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body: str


class GmailClient:

    def __init__(self) -> None:
        creds = get_credentials()
        self._service = build("gmail", "v1", credentials=creds)
        self._calendar_service = build("calendar", "v3", credentials=creds)
        logger.info("Gmail & Calendar API clients initialized.")

    def fetch_emails_since(
        self,
        since: datetime | None = None,
        max_results: int | None = None,
    ) -> list[EmailDict]:
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
            logger.info("First run — fetching emails from last 24 hours.")

        max_results = max_results or settings.MAX_EMAILS_PER_RUN
        query = self._build_query(since)
        logger.info("Fetching emails with query: %s (max: %d)", query, max_results)

        message_ids = self._list_messages(query, max_results)

        if not message_ids:
            logger.info("No new emails found.")
            return []

        logger.info("Found %d new email(s). Fetching details...", len(message_ids))

        emails = []
        for msg_ref in message_ids:
            try:
                parsed = self._fetch_and_parse(msg_ref["id"])
                if parsed:
                    emails.append(parsed)
            except Exception as e:
                logger.warning("Skipping message %s — parse error: %s", msg_ref["id"], e)

        logger.info("Successfully parsed %d email(s).", len(emails))
        return emails

    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def mark_as_read(self, message_ids: list[str]) -> None:
        """Mark a list of Gmail message IDs as read by removing the UNREAD label."""
        if not message_ids:
            return

        try:
            self._service.users().messages().batchModify(
                userId="me",
                body={
                    "ids": message_ids,
                    "removeLabelIds": ["UNREAD"]
                }
            ).execute()
            logger.info("Successfully marked %d message(s) as read in Gmail.", len(message_ids))
        except HttpError as e:
            logger.error("Gmail API error marking messages as read: %s", e)
            raise

    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def send_reply(self, original_message_id: str, recipient: str, subject: str, body: str) -> None:
        """Send an email reply to Gmail."""
        from email.mime.text import MIMEText
        import base64

        message = MIMEText(body)
        message["to"] = recipient
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        message["subject"] = subject
        message["In-Reply-To"] = original_message_id
        message["References"] = original_message_id

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        try:
            self._service.users().messages().send(
                userId="me",
                body={"raw": raw, "threadId": original_message_id}
            ).execute()
            logger.info("Successfully sent reply to %s.", recipient)
        except HttpError as e:
            logger.error("Gmail API error sending reply: %s", e)
            raise

    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def create_calendar_event(self, title: str, description: str, start_time: str, end_time: str | None = None) -> str:
        """Create a Google Calendar event and return the event ID."""
        if not end_time:
            from datetime import datetime, timedelta
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = start_dt + timedelta(hours=1)
                end_time = end_dt.isoformat()
            except Exception:
                end_time = start_time

        event_body = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": start_time,
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "UTC",
            },
        }

        try:
            event = (
                self._calendar_service.events()
                .insert(calendarId="primary", body=event_body)
                .execute()
            )
            logger.info("Successfully created calendar event: %s", event.get("htmlLink"))
            return event["id"]
        except HttpError as e:
            logger.error("Google Calendar API error creating event: %s", e)
            raise

    def _build_query(self, since: datetime) -> str:
        epoch = int(since.timestamp())
        return f"after:{epoch} -from:me"

    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _list_messages(self, query: str, max_results: int) -> list[dict]:
        try:
            response = (
                self._service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )
            return response.get("messages", [])
        except HttpError as e:
            logger.error("Gmail API error listing messages: %s", e)
            raise

    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _fetch_and_parse(self, message_id: str) -> EmailDict | None:
        raw = (
            self._service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        return self._parse_message(raw)

    def _parse_message(self, raw: dict) -> EmailDict | None:
        try:
            headers = {
                h["name"].lower(): h["value"]
                for h in raw.get("payload", {}).get("headers", [])
            }
            return EmailDict(
                message_id=raw["id"],
                subject=headers.get("subject", "(no subject)"),
                sender=headers.get("from", "(unknown sender)"),
                date=headers.get("date", ""),
                snippet=raw.get("snippet", ""),
                body=self._extract_body(raw.get("payload", {})),
            )
        except Exception as e:
            logger.warning("Failed to parse message %s: %s", raw.get("id"), e)
            return None

    def _extract_body(self, payload: dict) -> str:
        body = self._find_part(payload, "text/plain")
        if not body:
            body = self._find_part(payload, "text/html")
        return self._clean_text(body)

    def _find_part(self, payload: dict, mime_type: str) -> str:
        if payload.get("mimeType") == mime_type:
            data = payload.get("body", {}).get("data", "")
            if data:
                return self._decode_base64(data)
        for part in payload.get("parts", []):
            result = self._find_part(part, mime_type)
            if result:
                return result
        return ""

    def _decode_base64(self, data: str) -> str:
        try:
            padded = data + "=" * (4 - len(data) % 4)
            return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning("Base64 decode failed: %s", e)
            return ""

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines()]
        cleaned = "\n".join(line for line in lines if line)
        if len(cleaned) > 2000:
            cleaned = cleaned[:2000] + "\n... [truncated]"
        return cleaned