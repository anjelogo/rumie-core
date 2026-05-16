"""
§V.28 sole writer of MinIO. Handlers ! call boto3/minio-py directly.

Presigned-URL host strategy: minio-py signs the URL against the endpoint
the client was constructed with. For Cloudflare-fronted uploads, signing
endpoint = public host (rumie.xyz), so the generated URL is reachable
externally and the SigV4 host header matches when CF forwards original Host.

bucket name is the path segment after the host. With bucket="assets" and
PUBLIC_ASSET_BASE="https://rumie.xyz/assets", the asset URL is
"{base}/{key}" which equals "{public_host}/{bucket}/{key}".
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from urllib.parse import urlparse
from uuid import uuid4

from minio import Minio

from app.core.config import settings

_DEFAULT_REGION = "us-east-1"

_VALID_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

PRESIGN_MAX_TTL_S = 900


class AssetKind(str, Enum):
    avatar = "avatar"
    listing_photo = "listing_photo"


_internal: Minio | None = None
_signer: Minio | None = None


def _parse_public() -> tuple[str, bool]:
    """Return (host, secure) parsed from settings.public_asset_base."""
    parsed = urlparse(settings.public_asset_base)
    if not parsed.netloc:
        raise ValueError("public_asset_base must include scheme + host")
    return parsed.netloc, parsed.scheme == "https"


def _internal_client() -> Minio:
    global _internal
    if _internal is None:
        _internal = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            region=_DEFAULT_REGION,
        )
    return _internal


def _signer_client() -> Minio:
    global _signer
    if _signer is None:
        host, secure = _parse_public()
        _signer = Minio(
            host,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=secure,
            region=_DEFAULT_REGION,
        )
    return _signer


def bucket_exists() -> bool:
    return _internal_client().bucket_exists(settings.minio_bucket)


def ensure_bucket() -> None:
    c = _internal_client()
    if not c.bucket_exists(settings.minio_bucket):
        c.make_bucket(settings.minio_bucket)


def asset_url(key: str) -> str:
    """§V.19 absolute URL via Cloudflare ingress."""
    base = settings.public_asset_base.rstrip("/")
    return f"{base}/{key}"


def _make_key(kind: AssetKind, content_type: str) -> str:
    ext = _VALID_CONTENT_TYPES[content_type]
    return f"{kind.value}/{uuid4().hex}.{ext}"


def presigned_put(kind: AssetKind, content_type: str) -> dict:
    """§V.18 TTL ≤ 900s. §V.19 returns absolute asset_url.

    Returns: {put_url, asset_url, key, expires_at}
    Raises: ValueError on unsupported content_type.
    """
    if content_type not in _VALID_CONTENT_TYPES:
        raise ValueError(f"unsupported content_type: {content_type}")
    key = _make_key(kind, content_type)
    ttl = timedelta(seconds=min(settings.presign_ttl_s, PRESIGN_MAX_TTL_S))
    put_url = _signer_client().presigned_put_object(
        settings.minio_bucket, key, expires=ttl
    )
    return {
        "put_url": put_url,
        "asset_url": asset_url(key),
        "key": key,
        "expires_at": (datetime.now(timezone.utc) + ttl).isoformat(),
    }
