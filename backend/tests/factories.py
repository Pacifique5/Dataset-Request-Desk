"""Small helpers to create test data and authenticate as a given user."""

from itertools import count

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models import Role, User

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
