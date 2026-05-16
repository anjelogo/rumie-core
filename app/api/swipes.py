from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import require_group_admin
from app.models.group import RoommateGroup
from app.services.matching import SelfSwipeError, handle_swipe
from app.schemas.swipe import SwipeIn, SwipeOut

router = APIRouter(tags=["swipes"])


@router.post("/swipes")
async def post_swipe(
    body: SwipeIn,
    group: RoommateGroup = Depends(require_group_admin),
) -> SwipeOut:
    try:
        result = await handle_swipe(
            swiper_group=group,
            target_id=body.target_id,
            target_type=body.target_type,
            direction=body.direction,
        )
    except SelfSwipeError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    return SwipeOut(**result)
