"""§V.21 ∀ JSON response keys snake_case."""
import re

from app.schemas.auth import RegisterOut, TokensOut, UserOut
from app.schemas.conversation import ConversationOut, MessageOut
from app.schemas.group import GroupOut
from app.schemas.inquiry import InquiryOut
from app.schemas.invite import InviteOut
from app.schemas.listing import ListingOut
from app.schemas.swipe import SwipeOut

SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")

SCHEMAS = [
    UserOut, TokensOut, RegisterOut,
    GroupOut, InviteOut, ListingOut,
    SwipeOut, InquiryOut,
    ConversationOut, MessageOut,
]


def test_all_out_schemas_snake_case():
    for schema in SCHEMAS:
        json_schema = schema.model_json_schema()
        props = json_schema.get("properties", {})
        for name in props:
            assert SNAKE.match(name), f"{schema.__name__}.{name} not snake_case"


def test_no_alias_generators():
    for schema in SCHEMAS:
        cfg = getattr(schema, "model_config", {}) or {}
        assert cfg.get("alias_generator") is None, (
            f"{schema.__name__} has alias_generator set"
        )
