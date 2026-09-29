from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_is_hashed_with_argon2id_and_verifies():
    h = hash_password("s3cret!")
    assert h.startswith("$argon2id$")
    assert "s3cret!" not in h
    assert verify_password("s3cret!", h)
    assert not verify_password("wrong", h)


def test_verify_password_for_unknown_user_is_false():
    assert verify_password("anything", None) is False


def test_token_roundtrip():
    assert decode_access_token(create_access_token(42)) == 42


def test_expired_token_is_rejected():
    s = get_settings()
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    token = jwt.encode({"sub": "1", "exp": past}, s.jwt_secret, algorithm=s.jwt_algorithm)
    assert decode_access_token(token) is None


def test_token_signed_with_other_key_is_rejected():
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    token = jwt.encode({"sub": "1", "exp": future}, "x" * 32)
    assert decode_access_token(token) is None


def test_unsigned_alg_none_token_is_rejected():
    token = jwt.encode({"sub": "1", "exp": 9_999_999_999}, key=None, algorithm="none")
    assert decode_access_token(token) is None
