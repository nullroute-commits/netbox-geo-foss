"""Pytest configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.core.config import Settings, get_settings
from src.core.database import Base, get_db


# Override settings for testing
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Return test settings."""
    return Settings(
        environment="testing",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/15",
        secret_key="test-secret-key",
        debug=True,
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_settings):
    """Create test database engine."""
    engine = create_async_engine(
        str(test_settings.database_url),
        poolclass=StaticPool,
        echo=test_settings.database_echo,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    TestSessionLocal = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client(test_session, test_settings) -> Generator[TestClient, None, None]:
    """Create test client."""
    # Override dependencies
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = lambda: test_session

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client) -> dict[str, str]:
    """Create authenticated headers."""
    # Create test user and get token
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201

    # Login to get token
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_test_data():
    """Reset test data before each test."""
    # Clear any test files
    test_upload_dir = "/tmp/test_uploads"
    if os.path.exists(test_upload_dir):
        import shutil

        shutil.rmtree(test_upload_dir)
    os.makedirs(test_upload_dir, exist_ok=True)

    yield

    # Cleanup after test
    if os.path.exists(test_upload_dir):
        import shutil

        shutil.rmtree(test_upload_dir)


# Markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
pytest.mark.security = pytest.mark.security
