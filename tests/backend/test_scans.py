"""Scan endpoint tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


async def get_token(client: AsyncClient) -> str:
    # Register a fresh test user
    import uuid
    email = f"scan_test_{uuid.uuid4().hex[:6]}@nexus.local"
    res = await client.post("/auth/register", json={
        "email": email,
        "username": f"SCANOP_{uuid.uuid4().hex[:4].upper()}",
        "password": "pass123",
    })
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_create_scan():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_token(client)
        res = await client.post(
            "/scan/",
            json={
                "name": "TEST-SCAN-01",
                "lat_min": -10.0, "lat_max": 0.0,
                "lon_min": -65.0, "lon_max": -50.0,
                "scan_type": "anomaly",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 202
        data = res.json()
        assert data["name"] == "TEST-SCAN-01"
        assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_scans():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await get_token(client)
        res = await client.get("/scan/", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert isinstance(res.json(), list)
