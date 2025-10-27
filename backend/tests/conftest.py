"""
Pytest configuration and fixtures for testing
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.main import app
from app.db.session import get_db, Base
from app.core.config import settings

# Test database URL (use a separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/bc_legal_test"


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio for async tests"""
    return "asyncio"


@pytest.fixture(scope="function")
async def db_engine():
    """Create a test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client"""

    # Override the get_db dependency to use our test database
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def base_url():
    """Base URL for API endpoints"""
    return "http://test/api/v1"


@pytest.fixture
def test_user_data():
    """Sample test user data"""
    return {
        "company_name": "Test Company",
        "admin_email": "test@example.com",
        "admin_password": "TestPassword123",
        "admin_first_name": "Test",
        "admin_last_name": "User"
    }


@pytest.fixture
async def registered_user(client, test_user_data):
    """Create and return a registered test user"""
    response = await client.post(
        "/api/v1/auth/register",
        json=test_user_data
    )
    assert response.status_code == 201
    return response.json()
