"""
FastAPI backend for the Email Agent UI.
Serves the React frontend and exposes API endpoints.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import logger
from app.database import init_db
from api.routes import emails, agent, stats, settings, tasks, calendar, drafts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("Starting Email Agent API...")
    init_db()
    yield
    logger.info("Shutting down Email Agent API...")


app = FastAPI(
    title="Email Agent API",
    description="Autonomous Gmail classification agent",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ────────────────────────────────────────────────────────────────
app.include_router(emails.router,   prefix="/api/emails",   tags=["emails"])
app.include_router(agent.router,    prefix="/api/agent",    tags=["agent"])
app.include_router(stats.router,    prefix="/api/stats",    tags=["stats"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(tasks.router,    prefix="/api/tasks",    tags=["tasks"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(drafts.router,   prefix="/api/drafts",   tags=["drafts"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}