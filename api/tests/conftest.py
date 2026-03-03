"""
Pytest configuration and fixtures for API testing.

This module provides reusable fixtures for testing the Mining Farm Monitoring API
using httpx AsyncClient. The key learning points are:

1. httpx.AsyncClient maintains a cookie jar automatically
2. After login, the JWT cookie is stored and sent with subsequent requests
3. Different client fixtures provide pre-authenticated sessions for each role

Usage:
    pytest api/tests/ -v
    pytest api/tests/test_auth.py -v
    pytest api/tests/ -v --cov=api
"""

import asyncio
from typing import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import async_session_maker, engine, Base
from api.main import app
from api.models.user import User, UserRole
from api.services.auth_service import AuthService


# Test database URL (you can use a separate test database)
TEST_BASE_URL = "http://test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a database session for tests.
    
    Creates tables before tests and drops them after.
    """
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as session:
        yield session
    
    # Drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an unauthenticated httpx AsyncClient.
    
    This client does not have any authentication cookies set.
    Use this for testing endpoints that don't require authentication,
    or for testing authentication error responses.
    
    Example:
        async def test_health(async_client):
            response = await async_client.get("/api/v1/health")
            assert response.status_code == 200
    """
    # Setup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create client with ASGI transport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=TEST_BASE_URL) as client:
        yield client
    
    # Teardown: drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def create_test_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    role: UserRole,
) -> User:
    """Helper to create a test user."""
    from api.schemas.auth import UserCreate
    
    user_data = UserCreate(
        username=username,
        email=email,
        password=password,
        role=role,
    )
    return await AuthService.create_user(db, user_data)


async def get_authenticated_client(
    username: str,
    password: str,
) -> AsyncClient:
    """
    Creates an httpx AsyncClient with authentication cookie.
    
    This demonstrates how httpx handles cookies:
    1. Make a POST request to /auth/login
    2. The response includes Set-Cookie header
    3. AsyncClient automatically stores the cookie
    4. Subsequent requests include the cookie
    
    Args:
        username: Username or email for login
        password: User password
        
    Returns:
        AsyncClient with JWT cookie set
    """
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url=TEST_BASE_URL)
    
    # Login to get cookie
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    
    if response.status_code != 200:
        raise ValueError(f"Login failed: {response.json()}")
    
    # The cookie is now stored in client.cookies
    # It will be sent automatically with subsequent requests
    return client


@pytest_asyncio.fixture(scope="function")
async def admin_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an httpx AsyncClient authenticated as admin user.
    
    Admin has full access to all operations including delete.
    
    Example:
        async def test_delete_farm(admin_client, created_farm):
            response = await admin_client.delete(f"/api/v1/farms/{created_farm['id']}")
            assert response.status_code == 204
    """
    # Setup database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create admin user
    async with async_session_maker() as db:
        await create_test_user(
            db,
            username="admin_user",
            email="admin@test.com",
            password="adminpassword123",
            role=UserRole.ADMIN,
        )
        await db.commit()
    
    # Get authenticated client
    client = await get_authenticated_client("admin_user", "adminpassword123")
    
    yield client
    
    await client.aclose()
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def operator_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an httpx AsyncClient authenticated as operator user.
    
    Operator can create/modify farms, miners, metrics, alerts
    but cannot delete.
    
    Example:
        async def test_create_farm(operator_client):
            response = await operator_client.post(
                "/api/v1/farms",
                json={"name": "Test Farm"}
            )
            assert response.status_code == 201
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as db:
        await create_test_user(
            db,
            username="operator_user",
            email="operator@test.com",
            password="operatorpass123",
            role=UserRole.OPERATOR,
        )
        await db.commit()
    
    client = await get_authenticated_client("operator_user", "operatorpass123")
    
    yield client
    
    await client.aclose()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def viewer_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an httpx AsyncClient authenticated as viewer user.
    
    Viewer has read-only access to all resources.
    
    Example:
        async def test_list_farms(viewer_client):
            response = await viewer_client.get("/api/v1/farms")
            assert response.status_code == 200
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as db:
        await create_test_user(
            db,
            username="viewer_user",
            email="viewer@test.com",
            password="viewerpass123",
            role=UserRole.VIEWER,
        )
        await db.commit()
    
    client = await get_authenticated_client("viewer_user", "viewerpass123")
    
    yield client
    
    await client.aclose()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def created_farm(operator_client: AsyncClient) -> AsyncGenerator[dict, None]:
    """
    Creates a test farm and yields it, then deletes after test.
    
    Example:
        async def test_get_farm(viewer_client, created_farm):
            response = await viewer_client.get(f"/api/v1/farms/{created_farm['id']}")
            assert response.status_code == 200
    """
    # Create farm
    response = await operator_client.post(
        "/api/v1/farms",
        json={
            "name": "Test Mining Farm",
            "location": "Test Location",
            "total_power_kw": 100.0,
            "status": "offline",
        },
    )
    assert response.status_code == 201
    farm = response.json()
    
    yield farm
    
    # Note: Cleanup happens automatically with table drop


@pytest_asyncio.fixture
async def created_miner(
    operator_client: AsyncClient, created_farm: dict
) -> AsyncGenerator[dict, None]:
    """
    Creates a test miner and yields it.
    
    Depends on created_farm fixture.
    """
    response = await operator_client.post(
        f"/api/v1/farms/{created_farm['id']}/miners",
        json={
            "name": "Test Miner",
            "model": "Antminer S19 Pro",
            "ip_address": "192.168.1.100",
            "status": "active",
        },
    )
    assert response.status_code == 201
    miner = response.json()
    
    yield miner
