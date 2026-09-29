from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Assignment(Base):
    """An episode assigned to a request.

    UNIQUE(episode_id) is the database-level guarantee that an episode belongs to at
    most one request at a time, even under concurrent operators. Unassigning deletes
    the row, freeing the episode for another request.
    """

    __tablename__ = "assignments"
    __table_args__ = (Index("ix_assignments_request", "request_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_requests.id", ondelete="CASCADE"), nullable=False
    )
    episode_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("episodes.id"), unique=True, nullable=False
    )
    assigned_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
