"""User persistence helpers shared by the API and the seed command."""

from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Role, User


def normalise_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == normalise_email(email)))


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    name: str,
    role: Role,
    organisation: str | None = None,
) -> User:
    user = User(
        email=normalise_email(email),
        password_hash=hash_password(password),
        name=name.strip(),
        role=role,
        organisation=organisation,
    )
    db.add(user)
    db.flush()
    return user


def seed_users(db: Session, records: Iterable[Mapping[str, Any]]) -> tuple[int, int]:
    """Idempotent: creates missing users, never overwrites existing ones.

    Returns (created, skipped_existing).
    """
    created = skipped = 0
    for rec in records:
        if get_user_by_email(db, rec["email"]):
            skipped += 1
            continue
        create_user(
            db,
            email=rec["email"],
            password=rec["password"],
            name=rec["name"],
            role=Role(rec["role"]),
            organisation=rec.get("organisation"),
        )
        created += 1
    return created, skipped
