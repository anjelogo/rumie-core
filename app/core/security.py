from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import bcrypt
import jwt

from app.core.config import settings


def _to_bcrypt_bytes(plain: str) -> bytes:
    return plain.encode("utf-8")[:72]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_to_bcrypt_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])


def make_access(user_id: UUID, role: str) -> str:
    now = datetime.now(timezone.utc)
    return _encode(
        {
            "sub": str(user_id),
            "role": role,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=settings.access_ttl_s)).timestamp()),
        }
    )


def make_refresh(user_id: UUID) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    jti = uuid4().hex
    exp = now + timedelta(seconds=settings.refresh_ttl_s)
    tok = _encode(
        {
            "sub": str(user_id),
            "type": "refresh",
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
    )
    return tok, jti, exp
