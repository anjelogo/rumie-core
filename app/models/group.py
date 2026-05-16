from datetime import datetime, timezone
from uuid import UUID, uuid4

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import IndexModel


class Preferences(BaseModel):
    budget: int | None = None
    gender_pref: str | None = None
    age_range: tuple[int, int] | None = None
    tags: list[str] = Field(default_factory=list)


class RoommateGroup(Document):
    id: UUID = Field(default_factory=uuid4)
    admin_id: UUID
    members: list[UUID]
    preferences: Preferences = Field(default_factory=Preferences)
    capacity: int = Field(default=1, ge=1)
    version: int = 0
    dissolved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "groups"
        indexes = [
            IndexModel("admin_id"),
            IndexModel("members"),
        ]
