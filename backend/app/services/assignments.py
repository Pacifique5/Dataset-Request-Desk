"""Episode browsing and assignment rules.

Rules (brief section 3):
- an episode belongs to at most one request at a time  -> UNIQUE(assignments.episode_id)
- only `good` / `usable` episodes can be assigned        -> checked here
- assignments change only while a request is in_progress (it is frozen once delivered)

Assigning is all-or-nothing: if any episode in the batch is invalid, nothing is
assigned and the error lists every offending id, so the operator can fix it in one go.
The request row is locked (SELECT ... FOR UPDATE) for the duration, which serialises
assignment against the "enough episodes to deliver" check.
"""

from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.models import (
    ASSIGNABLE_QUALITIES,
    Assignment,
    DatasetRequest,
    Episode,
    Quality,
    RequestStatus,
    User,
)
from app.services.events import publish_request_event
from app.services.requests import get_request


@dataclass(frozen=True, slots=True)
class EpisodeFilters:
    task_name: str | None = None
    quality: Quality | None = None
    robot_id: str | None = None
    available_only: bool = False


def list_episodes(
    db: Session, filters: EpisodeFilters, *, limit: int = 50, offset: int = 0
) -> tuple[list[tuple[Episode, int | None]], int]:
    stmt = select(Episode, Assignment.request_id).outerjoin(
        Assignment, Assignment.episode_id == Episode.id
    )
    if filters.task_name:
        stmt = stmt.where(Episode.task_name == " ".join(filters.task_name.split()).lower())
    if filters.quality:
        stmt = stmt.where(Episode.quality == filters.quality)
    if filters.robot_id:
        stmt = stmt.where(Episode.robot_id == filters.robot_id.strip().lower())
    if filters.available_only:
        stmt = stmt.where(
            Assignment.id.is_(None), Episode.quality.in_([q.value for q in ASSIGNABLE_QUALITIES])
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(Episode.recorded_at.desc(), Episode.id.desc()).limit(limit).offset(offset)
    ).all()
    return [(ep, req_id) for ep, req_id in rows], total


def _editable_request(db: Session, user: User, request_id: int) -> DatasetRequest:
    req = get_request(db, user, request_id, for_update=True)
    if req.status is not RequestStatus.IN_PROGRESS:
        raise ConflictError(
            f"Assignments can only change while a request is in_progress (it is {req.status.value})"
        )
    return req


def _fmt(ids) -> str:
    return ", ".join(sorted(ids))


def assign_episodes(db: Session, user: User, request_id: int, episode_ids: list[str]) -> int:
    """Assign episodes by public id. Returns how many were newly assigned."""
    req = _editable_request(db, user, request_id)
    wanted = {e.strip().upper() for e in episode_ids if e.strip()}
    if not wanted:
        raise BusinessRuleError("No episode ids given")

    rows = db.execute(
        select(Episode, Assignment.request_id)
        .outerjoin(Assignment, Assignment.episode_id == Episode.id)
        .where(Episode.episode_id.in_(wanted))
    ).all()
    found = {ep.episode_id: (ep, assigned_to) for ep, assigned_to in rows}

    if missing := wanted - found.keys():
        raise NotFoundError(f"Unknown episodes: {_fmt(missing)}")
    if bad := {eid for eid, (ep, _) in found.items() if ep.quality not in ASSIGNABLE_QUALITIES}:
        raise BusinessRuleError(f"Only good or usable episodes can be assigned: {_fmt(bad)}")
    if taken := {eid for eid, (_, rid) in found.items() if rid is not None and rid != req.id}:
        raise ConflictError(f"Already assigned to another request: {_fmt(taken)}")

    new = [ep for ep, rid in found.values() if rid is None]
    try:
        with db.begin_nested():  # savepoint: a lost race doesn't poison the session
            db.add_all(
                Assignment(request_id=req.id, episode_id=ep.id, assigned_by_id=user.id)
                for ep in new
            )
    except IntegrityError as exc:
        # Another operator assigned one of these between our check and our insert;
        # the UNIQUE constraint is the real guarantee.
        raise ConflictError("One or more episodes were just assigned elsewhere; retry") from exc
    if new:
        publish_request_event(db, req, "assignments_changed", user.id)
    return len(new)


def unassign_episode(db: Session, user: User, request_id: int, episode_id: str) -> None:
    req = _editable_request(db, user, request_id)
    ep_pk = select(Episode.id).where(Episode.episode_id == episode_id.strip().upper())
    result = db.execute(
        delete(Assignment).where(Assignment.request_id == req.id, Assignment.episode_id.in_(ep_pk))
    )
    if result.rowcount == 0:
        raise NotFoundError("Episode is not assigned to this request")
    publish_request_event(db, req, "assignments_changed", user.id)


def list_assignments(
    db: Session, user: User, request_id: int
) -> tuple[DatasetRequest, list[tuple[Assignment, Episode]]]:
    req = get_request(db, user, request_id)  # enforces client visibility
    rows = db.execute(
        select(Assignment, Episode)
        .join(Episode, Episode.id == Assignment.episode_id)
        .where(Assignment.request_id == req.id)
        .order_by(Assignment.assigned_at, Assignment.id)
    ).all()
    return req, [(a, e) for a, e in rows]
