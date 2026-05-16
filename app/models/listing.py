from datetime import datetime, timezone
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel


class Listing(Document):
    id: UUID = Field(default_factory=uuid4)
    landlord_id: UUID
    title: str
    description: str = ""
    rent: int = Field(ge=0)
    location: str
    photo_urls: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "listings"
        indexes = [
            IndexModel("landlord_id"),
        ]
