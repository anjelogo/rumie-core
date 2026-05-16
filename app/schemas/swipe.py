from uuid import UUID

from pydantic import BaseModel

from app.models.swipe import SwipeDirection, SwipeTargetType


class SwipeIn(BaseModel):
    target_id: UUID
    target_type: SwipeTargetType
    direction: SwipeDirection


class SwipeOut(BaseModel):
    matched: bool
    merge: dict | None = None
    inquiry: dict | None = None
    reason: str | None = None
