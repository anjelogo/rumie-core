from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel


class ConversationType(str, Enum):
    internal_group = "internal_group"
    landlord_inquiry = "landlord_inquiry"


class Conversation(Document):
    id: UUID = Field(default_factory=uuid4)
    type: ConversationType
    participants: list[UUID]
    group_id: UUID
    listing_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "conversations"
        indexes = [
            IndexModel("participants"),
            IndexModel("group_id"),
        ]
