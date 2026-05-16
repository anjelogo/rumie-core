from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.conversation import Conversation, ConversationType
from app.models.message import Message


class ConversationOut(BaseModel):
    id: UUID
    type: ConversationType
    participants: list[UUID]
    group_id: UUID
    listing_id: UUID | None

    @classmethod
    def from_doc(cls, c: Conversation) -> "ConversationOut":
        return cls(
            id=c.id,
            type=c.type,
            participants=c.participants,
            group_id=c.group_id,
            listing_id=c.listing_id,
        )


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    body: str
    ts: datetime

    @classmethod
    def from_doc(cls, m: Message) -> "MessageOut":
        return cls(
            id=m.id,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            body=m.body,
            ts=m.ts,
        )


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
