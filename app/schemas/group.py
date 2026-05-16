from uuid import UUID

from pydantic import BaseModel

from app.models.group import Preferences, RoommateGroup


class GroupOut(BaseModel):
    id: UUID
    admin_id: UUID
    members: list[UUID]
    preferences: Preferences
    capacity: int

    @classmethod
    def from_doc(cls, g: RoommateGroup) -> "GroupOut":
        return cls(
            id=g.id,
            admin_id=g.admin_id,
            members=g.members,
            preferences=g.preferences,
            capacity=g.capacity,
        )


class GroupPatch(BaseModel):
    preferences: Preferences | None = None
    capacity: int | None = None
