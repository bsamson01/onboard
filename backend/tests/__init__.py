# Test configuration and fixtures for the microfinance platform

import pytest
import asyncio
from typing import Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.database import get_async_session, Base
from app.config import settings

# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Global test fixtures
@pytest.fixture(scope="function")
async def test_db():
    """Create test database and tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    try:
        yield
    finally:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session(test_db):
    """Create database session for test."""
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture(scope="function")
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
async def async_client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Override dependency
async def override_get_async_session():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_async_session] = override_get_async_session