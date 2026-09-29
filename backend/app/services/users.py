"""User persistence helpers shared by the API and the seed command."""

from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models import Role, User
from app.schemas.auth import UserCreate, UserUpdate


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


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


def register_user(db: Session, data: UserCreate) -> User:
    if get_user_by_email(db, data.email):
        raise ConflictError("A user with this email already exists")
    return create_user(
        db,
        email=data.email,
        password=data.password,
        name=data.name,
        role=data.role,
        organisation=data.organisation,
    )


def update_user(db: Session, actor: User, user_id: int, data: UserUpdate) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    changes = data.model_dump(exclude_unset=True)
    # Guard against an admin locking themselves (and possibly everyone) out.
    if user.id == actor.id and (
        changes.get("is_active") is False or changes.get("role", Role.ADMIN) is not Role.ADMIN
    ):
        raise BusinessRuleError("You cannot deactivate yourself or remove your own admin role")
    for field, value in changes.items():
        setattr(user, field, value)
    db.flush()
    return user
