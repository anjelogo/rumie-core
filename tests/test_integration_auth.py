"""Integration: register/login/RBAC/solo-group.
Requires: mongo single-node RS up. Run with: RUN_INTEGRATION=1 pytest
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.db import get_client, init_db
from app.main import app
from app.models import all_models
from tests.conftest import integration

pytestmark = integration


@pytest.fixture(autouse=True)
async def _db():
    await init_db()
    for m in all_models():
        await m.get_motor_collection().delete_many({})
    yield
    for m in all_models():
        await m.get_motor_collection().delete_many({})


async def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_register_rumie_creates_solo_group():
    """§V.7 register(role=rumie) → solo RoommateGroup."""
    async with await _client() as c:
        r = await c.post(
            "/api/v1/auth/register",
            json={
                "email": "a@b.co",
                "password": "passwordpw",
                "role": "rumie",
                "age": 21,
                "gender": "male",
                "capacity": 3,
            },
        )
        assert r.status_code == 201, r.text
        token = r.json()["tokens"]["access"]
        g = await c.get(
            "/api/v1/groups/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert g.status_code == 200
        body = g.json()
        assert body["capacity"] == 3
        assert len(body["members"]) == 1
        assert body["admin_id"] == body["members"][0]


async def test_landlord_blocked_from_rumie_endpoints():
    """§V.2 landlord ∉ /discovery/*, /swipes, /groups/*."""
    async with await _client() as c:
        r = await c.post(
            "/api/v1/auth/register",
            json={
                "email": "ll@b.co",
                "password": "passwordpw",
                "role": "landlord",
                "age": 30,
                "gender": "female",
            },
        )
        assert r.status_code == 201
        token = r.json()["tokens"]["access"]
        h = {"Authorization": f"Bearer {token}"}
        for path in ["/api/v1/groups/me", "/api/v1/discovery/groups", "/api/v1/discovery/listings"]:
            resp = await c.get(path, headers=h)
            assert resp.status_code == 403, f"{path} got {resp.status_code}"

        resp = await c.post(
            "/api/v1/swipes",
            headers=h,
            json={
                "target_id": "00000000-0000-0000-0000-000000000000",
                "target_type": "group",
                "direction": "right",
            },
        )
        assert resp.status_code == 403
