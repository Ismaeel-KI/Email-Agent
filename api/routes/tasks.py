from fastapi import APIRouter, HTTPException
from api.models import TaskResponse, UpdateTaskRequest
from app.database import repository

router = APIRouter()


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(status: str | None = None):
    """List all extracted tasks."""
    return repository.get_tasks(status=status)


@router.post("/{task_id}/toggle", response_model=dict)
async def toggle_task(task_id: int, req: UpdateTaskRequest):
    """Toggle a task's completeness status ('todo' or 'done')."""
    try:
        repository.update_task_status(task_id, req.status)
        return {"success": True, "message": f"Task updated to {req.status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
