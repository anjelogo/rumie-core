from uuid import uuid4

import pytest

from app.models.group import RoommateGroup
from app.models.swipe import SwipeDirection, SwipeTargetType
from app.services.matching import SelfSwipeError, handle_swipe


async def test_self_swipe_rejected_before_db():
    """§V.9: target ≠ swiper. Pre-DB guard."""
    gid = uuid4()
    fake = RoommateGroup.model_construct(
        id=gid,
        admin_id=uuid4(),
        members=[uuid4()],
        capacity=2,
        version=0,
        dissolved=False,
    )
    with pytest.raises(SelfSwipeError):
        await handle_swipe(
            swiper_group=fake,
            target_id=gid,
            target_type=SwipeTargetType.group,
            direction=SwipeDirection.right,
        )
