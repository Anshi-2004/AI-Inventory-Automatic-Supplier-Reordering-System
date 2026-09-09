import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "Test@1234",
        "role": "INVENTORY_MANAGER",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["email"] == "test@example.com"
    assert data["role"] == "INVENTORY_MANAGER"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"name": "User", "email": "dup@test.com", "password": "Test@1234"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "name": "User", "email": "u@test.com", "password": "short",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/auth/register", json={
        "name": "Login User", "email": "login@test.com", "password": "Login@1234",
    })
    resp = await client.post("/auth/login", json={
        "email": "login@test.com", "password": "Login@1234",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/auth/register", json={
        "name": "User", "email": "bad@test.com", "password": "Good@1234",
    })
    resp = await client.post("/auth/login", json={
        "email": "bad@test.com", "password": "WrongPass",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, admin_token: str):
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    resp = await client.get("/products")
    assert resp.status_code == 403
