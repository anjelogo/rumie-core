from uuid import UUID

from pydantic import BaseModel

from app.models.inquiry import Inquiry, InquiryStatus


class InquiryOut(BaseModel):
    id: UUID
    group_id: UUID
    listing_id: UUID
    status: InquiryStatus

    @classmethod
    def from_doc(cls, inq: Inquiry) -> "InquiryOut":
        return cls(
            id=inq.id,
            group_id=inq.group_id,
            listing_id=inq.listing_id,
            status=inq.status,
        )
