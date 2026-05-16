from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    decode_token,
    hash_password,
    make_access,
    make_refresh,
    verify_password,
)


def test_password_roundtrip():
    pw = "correct horse battery staple"
    h = hash_password(pw)
    assert h != pw
    assert verify_password(pw, h)
    assert not verify_password("wrong", h)


def test_access_token_roundtrip():
    uid = uuid4()
    tok = make_access(uid, "rumie")
    payload = decode_token(tok)
    assert payload["sub"] == str(uid)
    assert payload["role"] == "rumie"
    assert payload["type"] == "access"


def test_access_token_ttl_matches_settings():
    uid = uuid4()
    tok = make_access(uid, "rumie")
    payload = decode_token(tok)
    span = payload["exp"] - payload["iat"]
    assert span == settings.access_ttl_s


def test_refresh_token_has_jti_and_ttl():
    uid = uuid4()
    tok, jti, exp = make_refresh(uid)
    payload = decode_token(tok)
    assert payload["type"] == "refresh"
    assert payload["jti"] == jti
    span = payload["exp"] - payload["iat"]
    assert span == settings.refresh_ttl_s
    assert exp > datetime.now(timezone.utc) + timedelta(seconds=settings.refresh_ttl_s - 5)


def test_decode_rejects_tampered():
    uid = uuid4()
    tok = make_access(uid, "rumie")
    bad = tok[:-2] + ("ab" if tok[-2:] != "ab" else "cd")
    with pytest.raises(jwt.PyJWTError):
        decode_token(bad)
