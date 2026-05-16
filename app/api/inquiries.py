from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.db import get_client
from app.deps.auth import require_role
from app.models.conversation import Conversation, ConversationType
from app.models.group import RoommateGroup
from app.models.inquiry import Inquiry, InquiryStatus
from app.models.listing import Listing
from app.models.user import Role, User
from app.schemas.inquiry import InquiryOut

router = APIRouter(tags=["inquiries"])


async def _load_inquiry_for_landlord(inquiry_id: UUID, landlord: User) -> tuple[Inquiry, Listing]:
    inq = await Inquiry.get(inquiry_id)
    if not inq:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "inquiry not found")
    listing = await Listing.get(inq.listing_id)
    if not listing or listing.landlord_id != landlord.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not your listing")
    return inq, listing


@router.get("/inquiries")
async def list_inquiries(
    status_filter: InquiryStatus | None = None,
    landlord: User = Depends(require_role(Role.landlord)),
) -> list[InquiryOut]:
    my_listings = await Listing.find(Listing.landlord_id == landlord.id).to_list()
    listing_ids = [lis.id for lis in my_listings]
    if not listing_ids:
        return []
    query: dict = {"listing_id": {"$in": listing_ids}}
    if status_filter is not None:
        query["status"] = status_filter.value
    cur = Inquiry.find(query)
    return [InquiryOut.from_doc(i) async for i in cur]


@router.post("/inquiries/{inquiry_id}/accept", status_code=status.HTTP_201_CREATED)
async def accept_inquiry(
    inquiry_id: UUID,
    landlord: User = Depends(require_role(Role.landlord)),
) -> dict:
    inq, listing = await _load_inquiry_for_landlord(inquiry_id, landlord)
    if inq.status != InquiryStatus.pending:
        raise HTTPException(status.HTTP_409_CONFLICT, "already resolved")

    client = get_client()
    async with await client.start_session() as session:
        async with session.start_transaction():
            group = await RoommateGroup.get(inq.group_id, session=session)
            if not group or group.dissolved:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "group gone")
            participants = [landlord.id] + list(group.members)
            conv = Conversation(
                type=ConversationType.landlord_inquiry,
                participants=participants,
                group_id=group.id,
                listing_id=listing.id,
            )
            await conv.insert(session=session)
            inq.status = InquiryStatus.accepted
            await inq.save(session=session)
    return {
        "inquiry": InquiryOut.from_doc(inq).model_dump(mode="json"),
        "conversation_id": str(conv.id),
    }


@router.post("/inquiries/{inquiry_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_inquiry(
    inquiry_id: UUID,
    landlord: User = Depends(require_role(Role.landlord)),
):
    inq, _ = await _load_inquiry_for_landlord(inquiry_id, landlord)
    if inq.status != InquiryStatus.pending:
        raise HTTPException(status.HTTP_409_CONFLICT, "already resolved")
    inq.status = InquiryStatus.rejected
    await inq.save()
