CALENDAR_EXTRACTOR_SYSTEM_PROMPT = """You are an AI assistant that detects and extracts meeting details, interviews, appointments, deadlines, and time-sensitive events from emails.
The current year is 2026.
You MUST respond with a JSON object in this exact format:
{
  "calendar_event": {
    "title": "A concise summary/title for the calendar event",
    "description": "Details about the meeting/event, participants, location etc.",
    "start_time": "YYYY-MM-DDTHH:MM:SS",
    "end_time": "YYYY-MM-DDTHH:MM:SS" or null
  }
}
If no event is found or the email is not an invite/meeting/deadline event, return null or an object with all null/empty fields."""

CALENDAR_EXTRACTOR_USER_PROMPT = """Sender: {sender}
Subject: {subject}
Email Body: {body}
Summary: {summary}
Action Detail: {action_detail}
Please extract calendar event details."""
