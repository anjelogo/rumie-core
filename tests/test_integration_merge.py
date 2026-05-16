"""Integration: merge logic, capacity invariants, concurrency.
Requires: mongo single-node RS. Run with: RUN_INTEGRATION=1 pytest
"""
import asyncio
from uuid import uuid4

import pytest

from app.core.db import init_db
from app.models import all_models
from app.models.group import RoommateGroup
from app.models.swipe import Swipe, SwipeDirection, SwipeTargetType
from app.services.matching import handle_swipe
from tests.conftest import integration

pytestmark = integration


@pytest.fixture(autouse=True)
async def _db():
    await init_db()
    for m in all_models():
        await m.get_motor_collection().delete_many({})
    yield
    for m in all_models():
        await m.get_motor_collection().delete_many({})


async def _mk_group(capacity: int = 4, members_count: int = 1) -> RoommateGroup:
    admin = uuid4()
    members = [admin] + [uuid4() for _ in range(members_count - 1)]
    g = RoommateGroup(admin_id=admin, members=members, capacity=capacity)
    await g.insert()
    return g


async def test_mutual_right_swipe_merges_into_second_swiper():
    """§V.10, §V.11 absorber = second swiper."""
    a = await _mk_group(capacity=4, members_count=2)
    b = await _mk_group(capacity=4, members_count=2)

    # a swipes b right (first)
    await handle_swipe(a, b.id, SwipeTargetType.group, SwipeDirection.right)
    # b swipes a right (second = absorber)
    result = await handle_swipe(b, a.id, SwipeTargetType.group, SwipeDirection.right)

    assert result["matched"] is True
    assert result["merge"] is not None
    assert result["merge"]["absorber_id"] == str(b.id)
    assert result["merge"]["dissolved_id"] == str(a.id)

    b_after = await RoommateGroup.get(b.id)
    a_after = await RoommateGroup.get(a.id)
    assert len(b_after.members) == 4
    assert a_after.dissolved is True
    assert a_after.members == []


async def test_merge_denied_when_sum_over_max_capacity():
    """§V.10 (a + b) ≤ max(a.cap, b.cap)."""
    a = await _mk_group(capacity=2, members_count=2)
    b = await _mk_group(capacity=2, members_count=2)
    await handle_swipe(a, b.id, SwipeTargetType.group, SwipeDirection.right)
    result = await handle_swipe(b, a.id, SwipeTargetType.group, SwipeDirection.right)
    assert result["matched"] is True
    assert result["merge"] is None
    assert result["reason"] == "capacity"
    b_after = await RoommateGroup.get(b.id)
    assert b_after.dissolved is False
    assert len(b_after.members) == 2


async def test_concurrent_mutual_swipes_only_one_merge():
    """§V.12 atomic via txn. Concurrent triggers → at most one merge succeeds."""
    a = await _mk_group(capacity=4, members_count=2)
    b = await _mk_group(capacity=4, members_count=2)
    # both sides right-swipe simultaneously
    results = await asyncio.gather(
        handle_swipe(a, b.id, SwipeTargetType.group, SwipeDirection.right),
        handle_swipe(b, a.id, SwipeTargetType.group, SwipeDirection.right),
        return_exceptions=True,
    )
    merges = [r for r in results if isinstance(r, dict) and r.get("merge")]
    assert len(merges) == 1, results

    surviving = await RoommateGroup.find(RoommateGroup.dissolved == False).to_list()  # noqa: E712
    assert len(surviving) == 1
    assert len(surviving[0].members) == 4
