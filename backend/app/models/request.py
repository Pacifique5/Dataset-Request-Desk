from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RequestStatus
from app.models.mixins import CreatedAtMixin, str_enum
from app.models.user import User


class DatasetRequest(CreatedAtMixin, Base):
    __tablename__ = "dataset_requests"
    __table_args__ = (
        CheckConstraint("episodes_requested > 0", name="episodes_requested_positive"),
        Index("ix_dataset_requests_client_created", "client_id", "created_at"),
        Index("ix_dataset_requests_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    task_name: Mapped[str] = mapped_column(String(120), nullable=False)
    episodes_requested: Mapped[int] = mapped_column(nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[RequestStatus] = mapped_column(
        str_enum(RequestStatus, "request_status"),
        nullable=False,
        default=RequestStatus.SUBMITTED,
        server_default=RequestStatus.SUBMITTED.value,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    client: Mapped[User] = relationship(lazy="joined")
    events: Mapped[list["RequestStatusEvent"]] = relationship(
        back_populates="request",
        order_by="(RequestStatusEvent.changed_at, RequestStatusEvent.id)",
    )


class RequestStatusEvent(Base):
    """Append-only audit log: every status change, who made it and when."""

    __tablename__ = "request_status_events"
    __table_args__ = (
        Index("ix_request_status_events_request_changed", "request_id", "changed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_requests.id", ondelete="CASCADE"), nullable=False
    )
    # NULL for the creation event (nothing -> submitted).
    from_status: Mapped[RequestStatus | None] = mapped_column(
        str_enum(RequestStatus, "event_from_status")
    )
    to_status: Mapped[RequestStatus] = mapped_column(
        str_enum(RequestStatus, "event_to_status"), nullable=False
    )
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # Optional context, e.g. the client's reason for rejecting a delivery.
    note: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    request: Mapped[DatasetRequest] = relationship(back_populates="events")
    changed_by: Mapped[User] = relationship(lazy="joined")
