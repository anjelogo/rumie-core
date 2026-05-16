from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.mongo_uri,
            uuidRepresentation="standard",
            tz_aware=True,
        )
    return _client


async def init_db() -> None:
    from app.models import all_models

    client = get_client()
    await init_beanie(database=client[settings.mongo_db], document_models=all_models())
