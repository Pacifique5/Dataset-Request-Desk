"""Dataset request use-cases: create, list, read, change status.

Visibility rule: clients only ever see their own requests. For anyone else's request
we raise NotFound (404), not Forbidden, so a client can't probe which ids exist.
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.errors import (
    BusinessRuleError,
    InvalidTransitionError,
    NotFoundError,
    PermissionDeniedError,
)
from app.models import Assignment, DatasetRequest, RequestStatus, RequestStatusEvent, Role, User
from app.schemas.request import RequestCreate
from app.services.events import publish_request_event
from app.services.workflow import allowed_roles


@dataclass(frozen=True, slots=True)
class RequestWithCount:
    request: DatasetRequest
    episodes_assigned: int


def _assigned_count():
    return (
        select(func.count(Assignment.id))
        .where(Assignment.request_id == DatasetRequest.id)
        .correlate(DatasetRequest)
        .scalar_subquery()
    )


def _visible_to(stmt: Select, user: User) -> Select:
    return stmt.where(DatasetRequest.client_id == user.id) if user.role is Role.CLIENT else stmt


def create_request(db: Session, client: User, data: RequestCreate) -> DatasetRequest:
    if data.deadline < date.today():
        raise BusinessRuleError("deadline cannot be in the past")
    req = DatasetRequest(client_id=client.id, **data.model_dump())
    db.add(req)
    db.flush()
    db.add(
        RequestStatusEvent(
            request_id=req.id, from_status=None, to_status=req.status, changed_by_id=client.id
        )
    )
    db.flush()
    publish_request_event(db, req, "created", client.id)
    return req


def list_requests(
    db: Session,
    user: User,
    *,
    status: RequestStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[RequestWithCount], int]:
    base = _visible_to(select(DatasetRequest), user)
    if status is not None:
        base = base.where(DatasetRequest.status == status)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.execute(
        base.add_columns(_assigned_count())
        .order_by(DatasetRequest.created_at.desc(), DatasetRequest.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [RequestWithCount(r, n) for r, n in rows], total


def get_request(
    db: Session, user: User, request_id: int, *, for_update: bool = False
) -> DatasetRequest:
    stmt = _visible_to(select(DatasetRequest).where(DatasetRequest.id == request_id), user)
    if for_update:
        # Serialises concurrent status changes / assignments on the same request.
        stmt = stmt.with_for_update(of=DatasetRequest)
    req = db.scalar(stmt)
    if req is None:
        raise NotFoundError("Request not found")
    return req


def count_assigned(db: Session, request_id: int) -> int:
    return db.scalar(select(func.count()).where(Assignment.request_id == request_id)) or 0


def change_status(
    db: Session, user: User, request_id: int, target: RequestStatus, note: str | None = None
) -> DatasetRequest:
    req = get_request(db, user, request_id, for_update=True)
    current = req.status

    roles = allowed_roles(current, target)
    if roles is None:
        raise InvalidTransitionError(
            f"Cannot move a request from {current.value} to {target.value}"
        )
    if user.role not in roles:
        raise PermissionDeniedError(
            f"Your role cannot move a request from {current.value} to {target.value}"
        )
    # (Clients reach this point only for their own requests: get_request filtered them.)

    if target is RequestStatus.DELIVERED:
        assigned = count_assigned(db, req.id)
        if assigned < req.episodes_requested:
            raise BusinessRuleError(
                f"Cannot deliver: {assigned} of {req.episodes_requested} episodes assigned"
            )

    req.status = target
    db.add(
        RequestStatusEvent(
            request_id=req.id,
            from_status=current,
            to_status=target,
            changed_by_id=user.id,
            note=note,
        )
    )
    db.flush()
    db.refresh(req)
    publish_request_event(db, req, "status_changed", user.id)
    return req
