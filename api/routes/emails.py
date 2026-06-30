from fastapi import APIRouter, HTTPException
from api.models import EmailResponse
from app.database import get_latest_emails, get_email_by_id, get_emails_by_run

router = APIRouter()


@router.get("/", response_model=list[EmailResponse])
async def list_emails(category: str | None = None):
    """Return all emails from the latest run, optionally filtered by category."""
    emails = get_latest_emails()
    if category:
        emails = [e for e in emails if e.get("category") == category.lower()]
    return emails


@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(email_id: int):
    """Return a single email by ID."""
    email = get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.get("/run/{run_id}", response_model=list[EmailResponse])
async def list_emails_by_run(run_id: int):
    """Return all emails for a specific run."""
    emails = get_emails_by_run(run_id)
    if not emails:
        raise HTTPException(status_code=404, detail="Run not found")
    return emails