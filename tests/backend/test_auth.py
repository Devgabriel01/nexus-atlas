"""Basic auth endpoint tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register
        res = await client.post("/auth/register", json={
            "email": "test@nexus.local",
            "username": "TESTOP",
            "password": "testpass123",
        })
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test@nexus.local"

        # Login
        res = await client.post("/auth/login", json={
            "email": "test@nexus.local",
            "password": "testpass123",
        })
        assert res.status_code == 200
        assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_invalid_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/auth/login", json={
            "email": "ghost@nexus.local",
            "password": "wrong",
        })
        assert res.status_code == 401
