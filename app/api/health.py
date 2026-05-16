from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.db import get_client
from app.services.storage import bucket_exists

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    db_ok = False
    minio_ok = False
    try:
        await get_client().admin.command("ping")
        db_ok = True
    except Exception:
        pass
    try:
        minio_ok = bucket_exists()
    except Exception:
        pass
    body = {"db": "ok" if db_ok else "fail", "minio": "ok" if minio_ok else "fail"}
    status_code = 200 if (db_ok and minio_ok) else 503
    return JSONResponse(content=body, status_code=status_code)
