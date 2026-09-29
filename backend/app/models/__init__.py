"""Importing this package registers every table on Base.metadata (used by Alembic)."""

from app.models.assignment import Assignment
from app.models.enums import Quality, RequestStatus, Role
from app.models.episode import Episode, Robot
from app.models.request import DatasetRequest, RequestStatusEvent
from app.models.user import User

__all__ = [
    "Assignment",
    "DatasetRequest",
    "Episode",
    "Quality",
    "RequestStatus",
    "RequestStatusEvent",
    "Robot",
    "Role",
    "User",
]
