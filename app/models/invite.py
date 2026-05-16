from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel


class InviteStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class InviteRequest(Document):
    id: UUID = Field(default_factory=uuid4)
    group_id: UUID
    invitee_id: UUID
    status: InviteStatus = InviteStatus.pending
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "invites"
        indexes = [
            IndexModel("invitee_id"),
            IndexModel([("group_id", 1), ("invitee_id", 1), ("status", 1)]),
        ]
