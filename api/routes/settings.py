from fastapi import APIRouter
from api.models import SettingsResponse, SettingsUpdateRequest
from app.config import settings

router = APIRouter()


@router.get("/", response_model=SettingsResponse)
async def get_settings():
    """Return current agent settings."""
    return SettingsResponse(
        max_emails_per_run=settings.MAX_EMAILS_PER_RUN,
        poll_interval_minutes=settings.POLL_INTERVAL_MINUTES,
        log_level=settings.LOG_LEVEL,
        gemini_model=settings.GEMINI_MODEL,
        openrouter_model=settings.OPENROUTER_MODEL,
    )


@router.put("/", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdateRequest):
    """
    Update agent settings at runtime.
    Changes apply immediately without restart.
    """
    if body.max_emails_per_run is not None:
        settings.MAX_EMAILS_PER_RUN = body.max_emails_per_run
    if body.poll_interval_minutes is not None:
        settings.POLL_INTERVAL_MINUTES = body.poll_interval_minutes
    if body.log_level is not None:
        settings.LOG_LEVEL = body.log_level

    return SettingsResponse(
        max_emails_per_run=settings.MAX_EMAILS_PER_RUN,
        poll_interval_minutes=settings.POLL_INTERVAL_MINUTES,
        log_level=settings.LOG_LEVEL,
        gemini_model=settings.GEMINI_MODEL,
        openrouter_model=settings.OPENROUTER_MODEL,
    )