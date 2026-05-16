from datetime import datetime, timezone
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel


class RefreshToken(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    jti: str
    revoked: bool = False
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "refresh_tokens"
        indexes = [
            IndexModel("jti", unique=True),
            IndexModel("user_id"),
        ]
