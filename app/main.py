from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Rumie.xyz", lifespan=lifespan)
app.include_router(api_router)
