from datetime import datetime, timezone
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel


class Message(Document):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    sender_id: UUID
    body: str
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "messages"
        indexes = [
            IndexModel([("conversation_id", 1), ("ts", -1)]),
        ]
