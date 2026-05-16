from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import current_group, current_user, require_group_admin
from app.models.group import RoommateGroup
from app.models.user import User
from app.schemas.group import GroupOut, GroupPatch

router = APIRouter(tags=["groups"])


@router.get("/groups/me")
async def get_my_group(group: RoommateGroup = Depends(current_group)) -> GroupOut:
    return GroupOut.from_doc(group)


@router.patch("/groups/me")
async def patch_my_group(
    body: GroupPatch,
    group: RoommateGroup = Depends(require_group_admin),
) -> GroupOut:
    if body.preferences is not None:
        group.preferences = body.preferences
    if body.capacity is not None:
        if body.capacity < len(group.members):
            raise HTTPException(status.HTTP_409_CONFLICT, "capacity < members")
        group.capacity = body.capacity
    group.version += 1
    await group.save()
    return GroupOut.from_doc(group)


@router.post("/groups/me/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    user: User = Depends(current_user),
    group: RoommateGroup = Depends(current_group),
):
    if group.admin_id == user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "admin cannot leave; transfer first")
    if user.id not in group.members:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not in group")
    group.members.remove(user.id)
    group.version += 1
    await group.save()
    solo = RoommateGroup(admin_id=user.id, members=[user.id], capacity=1)
    await solo.insert()
