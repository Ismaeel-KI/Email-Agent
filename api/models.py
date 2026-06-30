from pydantic import BaseModel
from typing import Optional


class EmailResponse(BaseModel):
    id: int
    run_id: int
    message_id: str
    subject: str
    sender: str
    date: Optional[str] = None
    snippet: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    summary: Optional[str] = None
    requires_action: bool = False
    action_type: Optional[str] = None
    action_detail: Optional[str] = None
    deadline: Optional[str] = None
    skipped: bool = False
    error: Optional[str] = None
    created_at: Optional[str] = None


class RunResponse(BaseModel):
    id: int
    run_at: str
    email_count: int
    action_count: int
    ads_count: int
    error_count: int


class CategoryStat(BaseModel):
    category: str
    count: int


class DailyVolume(BaseModel):
    day: str
    count: int


class TopSender(BaseModel):
    sender: str
    count: int


class StatsResponse(BaseModel):
    latest_run: Optional[RunResponse] = None
    category_breakdown: list[CategoryStat]
    daily_volume: list[DailyVolume]
    action_rate: float
    action_count: int
    total_emails: int
    top_senders: list[TopSender]
    total_runs: int
    all_time_emails: int


class AgentStatusResponse(BaseModel):
    is_running: bool
    last_run: Optional[str] = None
    last_run_email_count: Optional[int] = None


class AgentRunResponse(BaseModel):
    success: bool
    message: str
    run_id: Optional[int] = None
    email_count: Optional[int] = None


class SettingsResponse(BaseModel):
    max_emails_per_run: int
    poll_interval_minutes: int
    log_level: str
    gemini_model: str
    openrouter_model: str


class SettingsUpdateRequest(BaseModel):
    max_emails_per_run: Optional[int] = None
    poll_interval_minutes: Optional[int] = None
    log_level: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    email_id: int
    title: str
    description: Optional[str] = None
    priority: str
    deadline: Optional[str] = None
    status: str
    created_at: str


class UpdateTaskRequest(BaseModel):
    status: str


class CalendarEventResponse(BaseModel):
    id: int
    email_id: int
    title: str
    description: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    status: str
    event_id: Optional[str] = None
    created_at: str


class DraftResponse(BaseModel):
    id: int
    email_id: int
    message_id: str
    subject: str
    recipient: str
    body: str
    status: str
    email_subject: Optional[str] = None
    email_sender: Optional[str] = None
    email_body: Optional[str] = None
    created_at: str


class SendReplyRequest(BaseModel):
    body: str