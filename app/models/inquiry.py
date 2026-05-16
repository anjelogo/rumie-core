from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel


class InquiryStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class Inquiry(Document):
    id: UUID = Field(default_factory=uuid4)
    group_id: UUID
    listing_id: UUID
    status: InquiryStatus = InquiryStatus.pending
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "inquiries"
        indexes = [
            IndexModel([("group_id", 1), ("listing_id", 1)], unique=True),
            IndexModel("status"),
        ]
