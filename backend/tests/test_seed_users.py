import json
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import Role, User
from app.services.users import create_user, seed_users

SEED_FILE = Path(__file__).resolve().parents[2] / "seed" / "users.json"


def _records():
    return json.loads(SEED_FILE.read_text(encoding="utf-8"))


def test_seed_creates_all_users_with_hashed_passwords(db):
    created, skipped = seed_users(db, _records())
    assert (created, skipped) == (5, 0)
    admin = db.scalar(select(User).where(User.email == "admin@example.com"))
    assert admin.role is Role.ADMIN
    assert admin.password_hash != "admin123"


def test_seed_is_idempotent(db):
    seed_users(db, _records())
    created, skipped = seed_users(db, _records())
    assert (created, skipped) == (0, 5)
    assert db.scalar(select(func.count()).select_from(User)) == 5


def test_email_uniqueness_is_case_insensitive_in_the_database(db):
    create_user(db, email="a@x.com", password="pw", name="A", role=Role.CLIENT)
    with pytest.raises(IntegrityError):
        # Bypass the service's normalisation to prove the DB itself enforces it.
        db.add(User(email="A@X.COM", password_hash="h", name="A2", role=Role.CLIENT))
        db.flush()
