from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import Quality


class ImportRowError(BaseModel):
    line: int
    episode_id: str | None
    reason: str
    detail: str


class ImportReportOut(BaseModel):
    rows_read: int
    imported: int
    skipped: int
    skipped_by_reason: dict[str, int]
    errors: list[ImportRowError]
    errors_truncated: bool


class EpisodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    episode_id: str
    robot_id: str
    task_name: str
    recorded_at: datetime
    duration_seconds: int
    operator_name: str | None
    quality: Quality
    assigned_request_id: int | None = None


class EpisodePage(BaseModel):
    items: list[EpisodeOut]
    total: int
    limit: int
    offset: int


class AssignIn(BaseModel):
    # Public episode ids (e.g. "EP-00011"); all-or-nothing, max 500 per call.
    episode_ids: list[str] = Field(min_length=1, max_length=500)


class AssignmentOut(BaseModel):
    episode: EpisodeOut
    assigned_at: datetime
    assigned_by_id: int


class AssignmentList(BaseModel):
    request_id: int
    episodes_requested: int
    episodes_assigned: int
    items: list[AssignmentOut]
