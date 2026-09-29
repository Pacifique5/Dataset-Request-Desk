"""Small helpers to create test data and authenticate as a given user."""

from datetime import date, datetime, timedelta, timezone
from itertools import count

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models import (
    Assignment,
    DatasetRequest,
    Episode,
    Quality,
    RequestStatus,
    Role,
    User,
)

_seq = count(1)
# Hashing is deliberately slow; tests reuse one precomputed hash for "password".
_PASSWORD_HASH = hash_password("password")


def make_user(db: Session, role: Role = Role.CLIENT, **overrides) -> User:
    n = next(_seq)
    user = User(
        email=overrides.pop("email", f"user{n}@test.local"),
        name=overrides.pop("name", f"User {n}"),
        role=role,
        password_hash=_PASSWORD_HASH,
        **overrides,
    )
    db.add(user)
    db.flush()
    return user


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def make_episode(db: Session, quality: Quality = Quality.GOOD, **overrides) -> Episode:
    n = next(_seq)
    ep = Episode(
        episode_id=overrides.pop("episode_id", f"EP-T{n:06d}"),
        robot_id=overrides.pop("robot_id", "arm-01"),
        task_name=overrides.pop("task_name", "pick cup"),
        recorded_at=overrides.pop("recorded_at", datetime(2026, 8, 1, 12, tzinfo=timezone.utc)),
        duration_seconds=overrides.pop("duration_seconds", 30),
        operator_name=overrides.pop("operator_name", "Eric"),
        quality=quality,
        **overrides,
    )
    db.add(ep)
    db.flush()
    return ep


def make_request(
    db: Session,
    client: User,
    status: RequestStatus = RequestStatus.SUBMITTED,
    episodes_requested: int = 1,
    **overrides,
) -> DatasetRequest:
    req = DatasetRequest(
        client_id=client.id,
        task_name=overrides.pop("task_name", "pick cup"),
        episodes_requested=episodes_requested,
        deadline=overrides.pop("deadline", date.today() + timedelta(days=30)),
        status=status,
        **overrides,
    )
    db.add(req)
    db.flush()
    return req


def assign(db: Session, req: DatasetRequest, ep: Episode, by: User) -> Assignment:
    a = Assignment(request_id=req.id, episode_id=ep.id, assigned_by_id=by.id)
    db.add(a)
    db.flush()
    return a
