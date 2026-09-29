from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import RequestStatus


class RequestCreate(BaseModel):
    task_name: str = Field(min_length=1, max_length=120)
    episodes_requested: int = Field(gt=0, le=100_000)
    deadline: date
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("task_name")
    @classmethod
    def _normalise_task(cls, v: str) -> str:
        # Same normalisation as the importer, so requests and episodes match.
        v = " ".join(v.split()).lower()
        if not v:
            raise ValueError("task_name must not be blank")
        return v


class TransitionIn(BaseModel):
    to_status: RequestStatus
    note: str | None = Field(default=None, max_length=2000)


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    organisation: str | None = None


class StatusEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: RequestStatus | None
    to_status: RequestStatus
    changed_by: UserBrief
    changed_at: datetime
    note: str | None


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client: UserBrief
    task_name: str
    episodes_requested: int
    episodes_assigned: int
    deadline: date
    notes: str | None
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    allowed_transitions: list[RequestStatus] = []


class RequestDetail(RequestOut):
    events: list[StatusEventOut]


class RequestPage(BaseModel):
    items: list[RequestOut]
    total: int
    limit: int
    offset: int
