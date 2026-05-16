from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel


class SwipeTargetType(str, Enum):
    group = "group"
    listing = "listing"


class SwipeDirection(str, Enum):
    left = "left"
    right = "right"


class Swipe(Document):
    id: UUID = Field(default_factory=uuid4)
    swiper_group_id: UUID
    target_id: UUID
    target_type: SwipeTargetType
    direction: SwipeDirection
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "swipes"
        indexes = [
            IndexModel(
                [("swiper_group_id", 1), ("target_id", 1), ("target_type", 1)],
                unique=True,
            ),
            IndexModel(
                [("target_id", 1), ("target_type", 1), ("direction", 1)],
            ),
        ]
