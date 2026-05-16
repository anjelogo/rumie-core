from app.models.conversation import Conversation
from app.models.group import RoommateGroup
from app.models.inquiry import Inquiry
from app.models.invite import InviteRequest
from app.models.listing import Listing
from app.models.message import Message
from app.models.swipe import Swipe
from app.models.token import RefreshToken
from app.models.user import User


def all_models():
    return [
        User,
        RoommateGroup,
        Listing,
        Swipe,
        InviteRequest,
        Inquiry,
        Conversation,
        Message,
        RefreshToken,
    ]


__all__ = [
    "User",
    "RoommateGroup",
    "Listing",
    "Swipe",
    "InviteRequest",
    "Inquiry",
    "Conversation",
    "Message",
    "RefreshToken",
    "all_models",
]
