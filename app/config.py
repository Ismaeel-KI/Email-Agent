import os
import logging
from pathlib import Path
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Load .env file from the project root
ROOT_DIR = Path(__file__).resolve().parent.parent
env_path = ROOT_DIR / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    GMAIL_USER_EMAIL: str = os.getenv("GMAIL_USER_EMAIL", "")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_EMAILS_PER_RUN: int = int(os.getenv("MAX_EMAILS_PER_RUN", "20"))

    # Models
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")

    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    
    # Credentials paths
    CREDENTIALS_DIR: Path = ROOT_DIR / 'credentials'
    CREDENTIALS_FILE: Path = CREDENTIALS_DIR / 'credentials.json'
    TOKEN_FILE: Path = CREDENTIALS_DIR / 'token.json'

    # Data paths
    DATA_DIR: Path = ROOT_DIR / 'data'
    STATE_FILE: Path = DATA_DIR / 'state.json'
    DIGEST_LOG: Path = DATA_DIR / 'digest.log'

    # Poll Interval
    POLL_INTERVAL_MINUTES: int = int(os.getenv("POLL_INTERVAL_MINUTES", "60"))

    def validate(self) -> None:
        missing = []
        if not self.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not self.OPENROUTER_API_KEY:
            missing.append("OPENROUTER_API_KEY")
        if not self.GMAIL_USER_EMAIL:
            missing.append("GMAIL_USER_EMAIL")
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Copy .env.example → .env and fill in the values."
            )

settings = Settings()

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("email-agent")
