from app.models.conversation import Conversation, ConversationType
from app.models.group import RoommateGroup


async def ensure_internal_group_conv(group: RoommateGroup, session=None) -> Conversation | None:
    """§V.16 internal_group conv ∀ group with ≥2 members. Idempotent.
    Returns the conv (created or updated) or None if members < 2.
    """
    if len(group.members) < 2:
        return None
    conv = await Conversation.find_one(
        Conversation.type == ConversationType.internal_group,
        Conversation.group_id == group.id,
        session=session,
    )
    if conv:
        if set(conv.participants) != set(group.members):
            conv.participants = list(group.members)
            await conv.save(session=session)
        return conv
    conv = Conversation(
        type=ConversationType.internal_group,
        participants=list(group.members),
        group_id=group.id,
    )
    await conv.insert(session=session)
    return conv
