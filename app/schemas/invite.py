from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.invite import InviteRequest, InviteStatus


class InviteCreate(BaseModel):
    invitee_email: EmailStr | None = None
    invitee_id: UUID | None = None


class InviteOut(BaseModel):
    id: UUID
    group_id: UUID
    invitee_id: UUID
    status: InviteStatus

    @classmethod
    def from_doc(cls, i: InviteRequest) -> "InviteOut":
        return cls(
            id=i.id,
            group_id=i.group_id,
            invitee_id=i.invitee_id,
            status=i.status,
        )
