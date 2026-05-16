from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.deps.auth import require_group_admin
from app.models.group import RoommateGroup
from app.models.listing import Listing
from app.models.swipe import Swipe, SwipeTargetType
from app.schemas.group import GroupOut
from app.schemas.listing import ListingOut

router = APIRouter(tags=["discovery"])


async def _swiped_target_ids(group_id: UUID, target_type: SwipeTargetType) -> list[UUID]:
    cur = Swipe.find(
        Swipe.swiper_group_id == group_id,
        Swipe.target_type == target_type,
    )
    return [s.target_id async for s in cur]


@router.get("/discovery/groups")
async def discover_groups(
    limit: int = Query(default=20, ge=1, le=100),
    group: RoommateGroup = Depends(require_group_admin),
) -> list[GroupOut]:
    excluded = await _swiped_target_ids(group.id, SwipeTargetType.group)
    excluded_ids = list(set(excluded) | {group.id})
    cur = RoommateGroup.find(
        {"_id": {"$nin": excluded_ids}, "dissolved": False},
    ).limit(limit)
    return [GroupOut.from_doc(g) async for g in cur]


@router.get("/discovery/listings")
async def discover_listings(
    limit: int = Query(default=20, ge=1, le=100),
    group: RoommateGroup = Depends(require_group_admin),
) -> list[ListingOut]:
    excluded = await _swiped_target_ids(group.id, SwipeTargetType.listing)
    cur = Listing.find({"_id": {"$nin": excluded}}).limit(limit)
    return [ListingOut.from_doc(lis) async for lis in cur]
