from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.deps.auth import current_user
from app.models.user import User
from app.services.storage import AssetKind, presigned_put

router = APIRouter(tags=["uploads"])


class PresignIn(BaseModel):
    kind: AssetKind
    content_type: str


class PresignOut(BaseModel):
    put_url: str
    asset_url: str
    key: str
    expires_at: str


@router.post("/uploads/presign")
async def presign(
    body: PresignIn,
    _: User = Depends(current_user),
) -> PresignOut:
    try:
        result = presigned_put(body.kind, body.content_type)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    return PresignOut(**result)
