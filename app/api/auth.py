from datetime import datetime, timezone
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.db import get_client
from app.core.security import (
    decode_token,
    hash_password,
    make_access,
    make_refresh,
    verify_password,
)
from app.deps.auth import current_user
from app.models.group import RoommateGroup
from app.models.token import RefreshToken
from app.models.user import Role, User
from app.schemas.auth import (
    LoginIn,
    RefreshIn,
    RegisterIn,
    RegisterOut,
    TokensOut,
    UserOut,
)

router = APIRouter(tags=["auth"])


async def _issue_tokens(user: User) -> TokensOut:
    access = make_access(user.id, user.role.value)
    refresh, jti, exp = make_refresh(user.id)
    await RefreshToken(user_id=user.id, jti=jti, expires_at=exp).insert()
    return TokensOut(access=access, refresh=refresh)


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn) -> RegisterOut:
    if await User.find_one(User.email == body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "email exists")

    user = User(
        email=body.email,
        phone=body.phone,
        hashed_password=hash_password(body.password),
        role=body.role,
        age=body.age,
        gender=body.gender,
    )
    client = get_client()
    async with await client.start_session() as session:
        async with session.start_transaction():
            await user.insert(session=session)
            if body.role == Role.rumie:
                group = RoommateGroup(
                    admin_id=user.id,
                    members=[user.id],
                    capacity=body.capacity,
                )
                await group.insert(session=session)
    tokens = await _issue_tokens(user)
    return RegisterOut(user=UserOut.from_doc(user), tokens=tokens)


@router.post("/auth/login")
async def login(body: LoginIn) -> TokensOut:
    user = await User.find_one(User.email == body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    return await _issue_tokens(user)


@router.post("/auth/refresh")
async def refresh(body: RefreshIn) -> TokensOut:
    try:
        payload = decode_token(body.refresh)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh")
    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "wrong token type")
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing jti")

    tok_doc = await RefreshToken.find_one(RefreshToken.jti == jti)
    if not tok_doc or tok_doc.revoked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh revoked")
    if tok_doc.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh expired")

    tok_doc.revoked = True
    await tok_doc.save()

    user = await User.get(UUID(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return await _issue_tokens(user)


@router.get("/auth/me")
async def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.from_doc(user)
