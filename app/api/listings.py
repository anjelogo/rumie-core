from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import current_user, require_role
from app.models.listing import Listing
from app.models.user import Role, User
from app.schemas.listing import ListingCreate, ListingOut, ListingPatch

router = APIRouter(tags=["listings"])


@router.post("/listings", status_code=status.HTTP_201_CREATED)
async def create_listing(
    body: ListingCreate,
    landlord: User = Depends(require_role(Role.landlord)),
) -> ListingOut:
    lis = Listing(landlord_id=landlord.id, **body.model_dump())
    await lis.insert()
    return ListingOut.from_doc(lis)


@router.get("/listings/{listing_id}")
async def get_listing(
    listing_id: UUID,
    _: User = Depends(current_user),
) -> ListingOut:
    lis = await Listing.get(listing_id)
    if not lis:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "listing not found")
    return ListingOut.from_doc(lis)


@router.patch("/listings/{listing_id}")
async def patch_listing(
    listing_id: UUID,
    body: ListingPatch,
    landlord: User = Depends(require_role(Role.landlord)),
) -> ListingOut:
    lis = await Listing.get(listing_id)
    if not lis:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "listing not found")
    if lis.landlord_id != landlord.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not owner")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(lis, k, v)
    await lis.save()
    return ListingOut.from_doc(lis)


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: UUID,
    landlord: User = Depends(require_role(Role.landlord)),
):
    lis = await Listing.get(listing_id)
    if not lis:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "listing not found")
    if lis.landlord_id != landlord.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not owner")
    await lis.delete()
