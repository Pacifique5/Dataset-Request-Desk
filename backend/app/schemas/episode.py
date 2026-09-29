from pydantic import BaseModel


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
