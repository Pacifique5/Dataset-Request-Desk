from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import Quality
from app.models.mixins import CreatedAtMixin, str_enum


class Robot(Base):
    """Reference table of known robots; episodes for unknown robots are rejected by FK."""

    __tablename__ = "robots"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)


class Episode(CreatedAtMixin, Base):
    __tablename__ = "episodes"
    __table_args__ = (
        CheckConstraint("duration_seconds > 0", name="duration_positive"),
        # Analytics: episodes per day per robot within a date range.
        Index("ix_episodes_recorded_at_robot", "recorded_at", "robot_id"),
        # Analytics: top task names by *good* episodes within a date range.
        Index(
            "ix_episodes_good_recorded_task",
            "recorded_at",
            "task_name",
            postgresql_where=text("quality = 'good'"),
        ),
        # Operator assignment screen filters by task + quality.
        Index("ix_episodes_task_quality", "task_name", "quality"),
    )

    # BIGINT: this table is expected to grow into the millions.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Natural key from the recording system; the import upserts on it (idempotency).
    episode_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    robot_id: Mapped[str] = mapped_column(ForeignKey("robots.id"), nullable=False)
    task_name: Mapped[str] = mapped_column(String(120), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(nullable=False)
    operator_name: Mapped[str | None] = mapped_column(String(120))
    quality: Mapped[Quality] = mapped_column(str_enum(Quality, "episode_quality"), nullable=False)
