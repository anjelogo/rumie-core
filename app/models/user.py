from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from beanie import Document
from pydantic import EmailStr, Field
from pymongo import IndexModel


class Role(str, Enum):
    rumie = "rumie"
    landlord = "landlord"


class Gender(str, Enum):
    male = "male"
    female = "female"
    nonbinary = "nonbinary"
    other = "other"


class User(Document):
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    phone: str | None = None
    hashed_password: str
    role: Role
    age: int = Field(ge=18)
    gender: Gender
    profile_photo_url: str | None = None
    token_version: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            IndexModel("email", unique=True),
        ]
