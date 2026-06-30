import asyncio
from fastapi import APIRouter, HTTPException
from api.models import CalendarEventResponse
from app.database import repository
from app.gmail import GmailClient

router = APIRouter()


@router.get("/", response_model=list[CalendarEventResponse])
async def list_calendar_events(status: str | None = None):
    """List all extracted calendar events."""
    return repository.get_calendar_events(status=status)


@router.post("/{event_id_db}/sync", response_model=dict)
async def sync_calendar_event(event_id_db: int):
    """Sync an approved event to Google Calendar."""
    event = repository.get_calendar_event_by_id(event_id_db)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    if event["status"] == "synced":
        return {"success": True, "message": "Event is already synced.", "event_id": event["event_id"]}

    try:
        client = GmailClient()
        google_event_id = await asyncio.to_thread(
            client.create_calendar_event,
            title=event["title"],
            description=event["description"] or "",
            start_time=event["start_time"],
            end_time=event["end_time"],
        )

        repository.update_calendar_event(event_id_db, "synced", google_event_id)
        return {"success": True, "message": "Event synced to Google Calendar successfully.", "event_id": google_event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
