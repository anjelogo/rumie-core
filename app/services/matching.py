from uuid import UUID

from pymongo.errors import ConnectionFailure, DuplicateKeyError, OperationFailure

from app.core.db import get_client
from app.models.conversation import Conversation, ConversationType
from app.models.group import RoommateGroup
from app.models.inquiry import Inquiry, InquiryStatus
from app.models.invite import InviteRequest, InviteStatus
from app.models.swipe import Swipe, SwipeDirection, SwipeTargetType
from app.services.conversations import ensure_internal_group_conv

MERGE_MAX_RETRIES = 3


class MergeCapacityError(Exception):
    pass


class SelfSwipeError(Exception):
    pass


async def handle_swipe(
    swiper_group: RoommateGroup,
    target_id: UUID,
    target_type: SwipeTargetType,
    direction: SwipeDirection,
) -> dict:
    """
    §V.9 reject self-target.
    §V.5 caller must be admin (enforced at endpoint).
    Persist swipe, then dispatch:
      - left → no effect.
      - right + listing → create/get pending Inquiry (§V.14).
      - right + group → look for mutual; if found + capacity OK → merge (§V.10-13).
    Returns dict for API: {matched, merge?, inquiry?, reason?}.
    """
    if target_type == SwipeTargetType.group and target_id == swiper_group.id:
        raise SelfSwipeError("cannot swipe own group")

    try:
        await Swipe(
            swiper_group_id=swiper_group.id,
            target_id=target_id,
            target_type=target_type,
            direction=direction,
        ).insert()
    except DuplicateKeyError:
        pass  # idempotent

    if direction == SwipeDirection.left:
        return {"matched": False}

    if target_type == SwipeTargetType.listing:
        inq = await Inquiry.find_one(
            Inquiry.group_id == swiper_group.id,
            Inquiry.listing_id == target_id,
        )
        if not inq:
            try:
                inq = Inquiry(group_id=swiper_group.id, listing_id=target_id)
                await inq.insert()
            except DuplicateKeyError:
                inq = await Inquiry.find_one(
                    Inquiry.group_id == swiper_group.id,
                    Inquiry.listing_id == target_id,
                )
        return {
            "matched": True,
            "inquiry": {"id": str(inq.id), "status": inq.status.value},
        }

    mutual = await Swipe.find_one(
        Swipe.swiper_group_id == target_id,
        Swipe.target_id == swiper_group.id,
        Swipe.target_type == SwipeTargetType.group,
        Swipe.direction == SwipeDirection.right,
    )
    if not mutual:
        return {"matched": False}

    for attempt in range(MERGE_MAX_RETRIES):
        try:
            result = await _merge_groups_txn(
                absorber_id=swiper_group.id, dissolved_id=target_id
            )
        except (OperationFailure, ConnectionFailure):
            if attempt == MERGE_MAX_RETRIES - 1:
                raise
            continue
        if result is None:
            return {"matched": True, "merge": None, "reason": "capacity"}
        return {"matched": True, "merge": result}

    return {"matched": True, "merge": None, "reason": "retry_exhausted"}


async def _merge_groups_txn(absorber_id: UUID, dissolved_id: UUID) -> dict | None:
    """
    §V.11 absorber = second swiper (caller). dissolved = the other.
    §V.10 capacity: (a + b) ≤ max(a.cap, b.cap).
    §V.12 atomic via mongo session txn.
    §V.13 re-point dissolved's swipes/invites/inquiries/conversations.
    §V.16 ensure absorber internal_group conv reflects new member list.
    """
    client = get_client()
    async with await client.start_session() as session:
        async with session.start_transaction():
            absorber = await RoommateGroup.get(absorber_id, session=session)
            dissolved = await RoommateGroup.get(dissolved_id, session=session)

            if not absorber or not dissolved:
                return None
            if absorber.dissolved or dissolved.dissolved:
                return None

            total = len(absorber.members) + len(dissolved.members)
            cap = max(absorber.capacity, dissolved.capacity)
            if total > cap:
                return None

            existing = set(absorber.members)
            absorber.members = absorber.members + [
                m for m in dissolved.members if m not in existing
            ]
            absorber.version += 1
            await absorber.save(session=session)

            dissolved.dissolved = True
            dissolved.members = []
            dissolved.version += 1
            await dissolved.save(session=session)

            await Swipe.find(Swipe.swiper_group_id == dissolved_id).update(
                {"$set": {"swiper_group_id": absorber_id}}, session=session
            )
            await InviteRequest.find(
                InviteRequest.group_id == dissolved_id,
                InviteRequest.status == InviteStatus.pending,
            ).update({"$set": {"group_id": absorber_id}}, session=session)
            await Inquiry.find(
                Inquiry.group_id == dissolved_id,
                Inquiry.status == InquiryStatus.pending,
            ).update({"$set": {"group_id": absorber_id}}, session=session)
            await Conversation.find(
                Conversation.group_id == dissolved_id,
                Conversation.type == ConversationType.landlord_inquiry,
            ).update(
                {
                    "$set": {
                        "group_id": absorber_id,
                        "participants": list(absorber.members),
                    }
                },
                session=session,
            )

            await ensure_internal_group_conv(absorber, session=session)

            dissolved_conv = await Conversation.find_one(
                Conversation.type == ConversationType.internal_group,
                Conversation.group_id == dissolved_id,
                session=session,
            )
            if dissolved_conv:
                await dissolved_conv.delete(session=session)

            return {
                "absorber_id": str(absorber_id),
                "dissolved_id": str(dissolved_id),
                "members": [str(m) for m in absorber.members],
            }
