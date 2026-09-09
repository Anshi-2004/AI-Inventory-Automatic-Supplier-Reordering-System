"""
pytest configuration and shared fixtures.
All external APIs (OpenRouter, Gmail) are mocked — no real calls made.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.base import Base
from app.database.session import get_db
from app.main import app

# ── In-memory SQLite for tests ─────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    """Register admin and return JWT token."""
    resp = await client.post("/auth/register", json={
        "name": "Test Admin",
        "email": "admin@test.com",
        "password": "Admin@1234",
        "role": "ADMIN",
    })
    assert resp.status_code == 201
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def manager_token(client: AsyncClient) -> str:
    """Register manager and return JWT token."""
    resp = await client.post("/auth/register", json={
        "name": "Test Manager",
        "email": "manager@test.com",
        "password": "Manager@1234",
        "role": "INVENTORY_MANAGER",
    })
    assert resp.status_code == 201
    return resp.json()["access_token"]
