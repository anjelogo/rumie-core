"""§V.18 TTL ≤ 900s. §V.19 absolute URL via Cloudflare ingress."""
import re
from urllib.parse import urlparse

import pytest

from app.core.config import settings
from app.services.storage import AssetKind, asset_url, presigned_put


def test_asset_url_is_absolute_with_public_base():
    key = "avatar/abc123.jpg"
    url = asset_url(key)
    assert url.startswith(settings.public_asset_base.rstrip("/"))
    parsed = urlparse(url)
    assert parsed.scheme in ("http", "https")
    assert parsed.netloc
    assert parsed.path.endswith(key)


def test_asset_url_default_points_to_rumie_assets():
    """Default config: PUBLIC_ASSET_BASE=https://rumie.xyz/assets."""
    url = asset_url("avatar/x.jpg")
    assert url == "https://rumie.xyz/assets/avatar/x.jpg"


def test_presigned_put_returns_required_keys():
    result = presigned_put(AssetKind.avatar, "image/jpeg")
    assert set(result.keys()) == {"put_url", "asset_url", "key", "expires_at"}
    assert result["asset_url"].startswith("https://rumie.xyz/assets/")
    assert re.match(r"^avatar/[0-9a-f]+\.jpg$", result["key"])
    assert urlparse(result["put_url"]).netloc == "rumie.xyz"


def test_presigned_put_rejects_unknown_content_type():
    with pytest.raises(ValueError):
        presigned_put(AssetKind.avatar, "application/octet-stream")


def test_presign_ttl_at_most_900s():
    assert settings.presign_ttl_s <= 900
