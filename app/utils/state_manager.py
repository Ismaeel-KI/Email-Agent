import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

logger = logging.getLogger("email-agent.state")


class StateManager:
    """
    Manages the polling state stored in data/state.json.
    Tracks the last_run timestamp so each cron run only
    fetches emails received since the previous run.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.STATE_FILE
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Create state.json with default content if it doesn't exist."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._write({"last_run": None})
            logger.info("Created state file at %s", self.path)

    def get_last_run(self) -> datetime | None:
        """
        Return the last_run timestamp as a UTC datetime, or None if first run.
        """
        data = self._read()
        raw = data.get("last_run")
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError) as e:
            logger.warning("Could not parse last_run '%s': %s — treating as first run.", raw, e)
            return None

    def save_last_run(self, dt: datetime | None = None) -> None:
        """
        Save the current UTC time (or a provided datetime) as last_run.
        """
        dt = dt or datetime.now(timezone.utc)
        data = self._read()
        data["last_run"] = dt.isoformat()
        self._write(data)
        logger.info("Saved last_run: %s", dt.isoformat())

    def _read(self) -> dict:
        try:
            text = self.path.read_text(encoding="utf-8").strip()
            if not text:
                return {"last_run": None}
            return json.loads(text)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read state file: %s — using defaults.", e)
            return {"last_run": None}

    def _write(self, data: dict) -> None:
        try:
            self.path.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8"
            )
        except OSError as e:
            logger.error("Failed to write state file: %s", e)
            raise