from uuid import UUID

from pydantic import BaseModel, Field

from app.models.listing import Listing


class ListingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    rent: int = Field(ge=0)
    location: str
    photo_urls: list[str] = Field(default_factory=list)


class ListingPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    rent: int | None = Field(default=None, ge=0)
    location: str | None = None
    photo_urls: list[str] | None = None


class ListingOut(BaseModel):
    id: UUID
    landlord_id: UUID
    title: str
    description: str
    rent: int
    location: str
    photo_urls: list[str]

    @classmethod
    def from_doc(cls, lis: Listing) -> "ListingOut":
        return cls(
            id=lis.id,
            landlord_id=lis.landlord_id,
            title=lis.title,
            description=lis.description,
            rent=lis.rent,
            location=lis.location,
            photo_urls=lis.photo_urls,
        )
