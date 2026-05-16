from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.db import get_client
from app.deps.auth import current_user, require_group_admin
from app.models.group import RoommateGroup
from app.models.invite import InviteRequest, InviteStatus
from app.models.user import Role, User
from app.schemas.invite import InviteCreate, InviteOut
from app.services.conversations import ensure_internal_group_conv

router = APIRouter(tags=["invites"])


@router.post("/groups/me/invites", status_code=status.HTTP_201_CREATED)
async def create_invite(
    body: InviteCreate,
    group: RoommateGroup = Depends(require_group_admin),
) -> InviteOut:
    if not body.invitee_email and not body.invitee_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "email or id required")

    if body.invitee_id:
        invitee = await User.get(body.invitee_id)
    else:
        invitee = await User.find_one(User.email == body.invitee_email)
    if not invitee or invitee.role != Role.rumie:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "rumie not found")
    if invitee.id in group.members:
        raise HTTPException(status.HTTP_409_CONFLICT, "already a member")

    existing = await InviteRequest.find_one(
        InviteRequest.group_id == group.id,
        InviteRequest.invitee_id == invitee.id,
        InviteRequest.status == InviteStatus.pending,
    )
    if existing:
        return InviteOut.from_doc(existing)

    inv = InviteRequest(group_id=group.id, invitee_id=invitee.id)
    await inv.insert()
    return InviteOut.from_doc(inv)


@router.post("/invites/{invite_id}/accept")
async def accept_invite(
    invite_id: UUID,
    user: User = Depends(current_user),
) -> InviteOut:
    inv = await InviteRequest.get(invite_id)
    if not inv or inv.invitee_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "invite not found")
    if inv.status != InviteStatus.pending:
        raise HTTPException(status.HTTP_409_CONFLICT, "already resolved")

    client = get_client()
    async with await client.start_session() as session:
        async with session.start_transaction():
            target = await RoommateGroup.get(inv.group_id, session=session)
            if not target or target.dissolved:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "group gone")
            if user.id in target.members:
                raise HTTPException(status.HTTP_409_CONFLICT, "already member")
            if len(target.members) + 1 > target.capacity:
                raise HTTPException(status.HTTP_409_CONFLICT, "capacity full")

            current = await RoommateGroup.find_one(
                RoommateGroup.members == user.id, session=session
            )

            target.members.append(user.id)
            target.version += 1
            await target.save(session=session)

            if current and current.id != target.id:
                if current.admin_id == user.id and len(current.members) == 1:
                    await current.delete(session=session)
                else:
                    current.members.remove(user.id)
                    current.version += 1
                    await current.save(session=session)

            await ensure_internal_group_conv(target, session=session)

            inv.status = InviteStatus.accepted
            await inv.save(session=session)

    return InviteOut.from_doc(inv)


@router.post("/invites/{invite_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_invite(invite_id: UUID, user: User = Depends(current_user)):
    inv = await InviteRequest.get(invite_id)
    if not inv or inv.invitee_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "invite not found")
    if inv.status != InviteStatus.pending:
        raise HTTPException(status.HTTP_409_CONFLICT, "already resolved")
    inv.status = InviteStatus.rejected
    await inv.save()
