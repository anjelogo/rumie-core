from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps.auth import current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import (
    ConversationOut,
    MessageIn,
    MessageOut,
)

router = APIRouter(tags=["conversations"])


@router.get("/conversations")
async def list_conversations(
    user: User = Depends(current_user),
) -> list[ConversationOut]:
    cur = Conversation.find(Conversation.participants == user.id)
    return [ConversationOut.from_doc(c) async for c in cur]


async def _load_conv_for_participant(conv_id: UUID, user: User) -> Conversation:
    conv = await Conversation.get(conv_id)
    if not conv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "conversation not found")
    if user.id not in conv.participants:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not a participant")
    return conv


@router.get("/conversations/{conv_id}/messages")
async def list_messages(
    conv_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    before: datetime | None = None,
    user: User = Depends(current_user),
) -> list[MessageOut]:
    await _load_conv_for_participant(conv_id, user)
    query: dict = {"conversation_id": conv_id}
    if before is not None:
        query["ts"] = {"$lt": before}
    cur = (
        Message.find(query)
        .sort("-ts")
        .limit(limit)
    )
    return [MessageOut.from_doc(m) async for m in cur]


@router.post("/conversations/{conv_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    conv_id: UUID,
    body: MessageIn,
    user: User = Depends(current_user),
) -> MessageOut:
    conv = await _load_conv_for_participant(conv_id, user)
    msg = Message(conversation_id=conv.id, sender_id=user.id, body=body.body)
    await msg.insert()
    return MessageOut.from_doc(msg)
