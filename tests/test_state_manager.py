"""
Tests for app/utils/state_manager.py
Uses a temp directory — no real state.json touched.
"""
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from app.utils.state_manager import StateManager


@pytest.fixture
def tmp_state_file(tmp_path: Path) -> Path:
    """Return a temp path for state.json."""
    return tmp_path / "state.json"


class TestStateManager:

    def test_creates_file_if_missing(self, tmp_state_file):
        sm = StateManager(path=tmp_state_file)
        assert tmp_state_file.exists()

    def test_get_last_run_returns_none_on_first_run(self, tmp_state_file):
        sm = StateManager(path=tmp_state_file)
        assert sm.get_last_run() is None

    def test_save_and_load_last_run(self, tmp_state_file):
        sm = StateManager(path=tmp_state_file)
        dt = datetime(2026, 6, 28, 18, 0, 0, tzinfo=timezone.utc)
        sm.save_last_run(dt)

        loaded = sm.get_last_run()
        assert loaded is not None
        assert loaded.year == 2026
        assert loaded.month == 6
        assert loaded.day == 28

    def test_save_last_run_defaults_to_now(self, tmp_state_file):
        sm = StateManager(path=tmp_state_file)
        before = datetime.now(timezone.utc)
        sm.save_last_run()
        after = datetime.now(timezone.utc)

        loaded = sm.get_last_run()
        assert loaded is not None
        assert before <= loaded <= after

    def test_handles_empty_state_file(self, tmp_state_file):
        tmp_state_file.write_text("")
        sm = StateManager(path=tmp_state_file)
        assert sm.get_last_run() is None

    def test_handles_corrupt_state_file(self, tmp_state_file):
        tmp_state_file.write_text("not valid json {{{{")
        sm = StateManager(path=tmp_state_file)
        assert sm.get_last_run() is None

    def test_handles_invalid_timestamp(self, tmp_state_file):
        tmp_state_file.write_text(json.dumps({"last_run": "not-a-date"}))
        sm = StateManager(path=tmp_state_file)
        assert sm.get_last_run() is None

    def test_adds_utc_timezone_if_missing(self, tmp_state_file):
        # Naive datetime string (no timezone info)
        tmp_state_file.write_text(json.dumps({"last_run": "2026-06-28T18:00:00"}))
        sm = StateManager(path=tmp_state_file)
        result = sm.get_last_run()
        assert result is not None
        assert result.tzinfo == timezone.utc