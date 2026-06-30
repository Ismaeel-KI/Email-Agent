import logging
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from app.config import settings

logger = logging.getLogger("email-agent.auth")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events"
]


def get_credentials() -> Credentials:
    creds: Credentials | None = None
    token_path: Path = settings.TOKEN_FILE
    credentials_path: Path = settings.CREDENTIALS_FILE

    # Step 1: Load existing token
    if token_path.exists() and token_path.stat().st_size > 2:
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if creds and not all(scope in creds.scopes for scope in SCOPES):
                logger.info("Token scopes do not match requested scopes. Re-authenticating.")
                creds = None
            else:
                logger.debug("Loaded existing token from %s", token_path)
        except Exception as e:
            logger.warning("Failed to load token.json: %s — will re-authenticate", e)
            creds = None

    # Step 2: Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            logger.info("Access token refreshed successfully.")
            _save_token(creds, token_path)
        except Exception as e:
            logger.warning("Token refresh failed: %s — will re-authenticate", e)
            creds = None

    # Step 3: Full OAuth flow if no valid creds
    if not creds or not creds.valid:
        logger.info("No valid credentials found. Starting OAuth flow...")
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path), SCOPES
        )
        creds = flow.run_local_server(port=0, open_browser=True, prompt="consent")
        _save_token(creds, token_path)
        logger.info("OAuth flow complete. Token saved to %s", token_path)

    return creds


def _save_token(creds: Credentials, token_path: Path) -> None:
    try:
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
        logger.debug("Token saved to %s", token_path)
    except Exception as e:
        logger.error("Failed to save token: %s", e)
        raise