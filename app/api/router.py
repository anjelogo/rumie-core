from fastapi import APIRouter

from app.api import (
    auth,
    conversations,
    discovery,
    groups,
    health,
    inquiries,
    invites,
    listings,
    swipes,
    uploads,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(groups.router)
api_router.include_router(invites.router)
api_router.include_router(listings.router)
api_router.include_router(discovery.router)
api_router.include_router(swipes.router)
api_router.include_router(inquiries.router)
api_router.include_router(conversations.router)
api_router.include_router(uploads.router)
