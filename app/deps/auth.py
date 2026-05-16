from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_token
from app.models.group import RoommateGroup
from app.models.user import Role, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def current_user(token: str | None = Depends(oauth2_scheme)) -> User:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing token")
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "wrong token type")
    user = await User.get(UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


def require_role(*allowed: Role):
    async def dep(user: User = Depends(current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "role forbidden")
        return user

    return dep


async def current_group(user: User = Depends(current_user)) -> RoommateGroup:
    if user.role != Role.rumie:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "rumie only")
    group = await RoommateGroup.find_one(RoommateGroup.members == user.id)
    if not group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no group")
    return group


async def require_group_admin(
    user: User = Depends(current_user),
    group: RoommateGroup = Depends(current_group),
) -> RoommateGroup:
    if group.admin_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")
    return group
