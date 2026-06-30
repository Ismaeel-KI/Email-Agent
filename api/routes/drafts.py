import asyncio
from fastapi import APIRouter, HTTPException
from api.models import DraftResponse, SendReplyRequest
from app.database import repository
from app.gmail import GmailClient

router = APIRouter()


@router.get("/pending", response_model=list[DraftResponse])
async def list_pending_drafts():
    """List all pending drafts."""
    return repository.get_pending_drafts()


@router.post("/{draft_id}/send", response_model=dict)
async def send_draft_reply(draft_id: int, req: SendReplyRequest):
    """Send the AI reply draft or user-edited reply text via Gmail."""
    draft = repository.get_draft_by_id(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found.")

    if draft["status"] == "sent":
        return {"success": True, "message": "Draft already sent."}

    try:
        client = GmailClient()
        await asyncio.to_thread(
            client.send_reply,
            original_message_id=draft["message_id"],
            recipient=draft["recipient"],
            subject=draft["subject"],
            body=req.body,
        )

        repository.update_draft(draft_id, "sent", req.body)
        return {"success": True, "message": "Reply sent successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{draft_id}/discard", response_model=dict)
async def discard_draft(draft_id: int):
    """Discard a pending draft."""
    try:
        repository.update_draft(draft_id, "discarded")
        return {"success": True, "message": "Draft discarded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
