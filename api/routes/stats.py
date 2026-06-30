from fastapi import APIRouter
from api.models import StatsResponse
from app.database import get_stats

router = APIRouter()


@router.get("/", response_model=StatsResponse)
async def get_statistics():
    """Return aggregate stats for the dashboard."""
    return get_stats()