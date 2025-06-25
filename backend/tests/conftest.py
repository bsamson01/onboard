"""
Pytest configuration and fixtures for comprehensive test suite.
"""

import pytest
import asyncio
import asyncpg
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.database import get_async_session, Base
from app.models.user import User, UserRole
from app.models.mfi_config import MFIInstitution, ExternalServiceConfig, ServiceType
from app.core.auth import get_password_hash
from tests.test_data_generator import EdgeCaseDataGenerator, create_edge_case_dataset

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

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

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
async def db_session(test_db) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for test."""
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture(scope="function")
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Override dependency
async def override_get_async_session():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_async_session] = override_get_async_session

# User fixtures
@pytest.fixture
async def test_user_data():
    """Standard test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """Create admin user for testing."""
    admin = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin

@pytest.fixture
async def regular_user(db_session: AsyncSession):
    """Create regular user for testing."""
    user = User(
        email="user@example.com",
        username="regularuser",
        hashed_password=get_password_hash("user123"),
        first_name="Regular",
        last_name="User",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def admin_token(admin_user, async_client: AsyncClient):
    """Get admin authentication token."""
    login_data = {
        "username": "admin@example.com",
        "password": "admin123"
    }
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    return response.json()["access_token"]

@pytest.fixture
async def user_token(regular_user, async_client: AsyncClient):
    """Get regular user authentication token."""
    login_data = {
        "username": "user@example.com",
        "password": "user123"
    }
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    return response.json()["access_token"]

# MFI configuration fixtures
@pytest.fixture
async def test_mfi_institution(db_session: AsyncSession, admin_user):
    """Create test MFI institution."""
    institution = MFIInstitution(
        code="TEST_MFI",
        name="Test Microfinance Institution",
        display_name="Test MFI",
        description="Test institution for automated testing",
        contact_email="test@testmfi.com",
        country="Kenya",
        business_model="individual_lending",
        minimum_credit_score=600,
        created_by_id=admin_user.id
    )
    db_session.add(institution)
    await db_session.commit()
    await db_session.refresh(institution)
    return institution

@pytest.fixture
async def test_scorecard_service(db_session: AsyncSession, test_mfi_institution, admin_user):
    """Create test scorecard service configuration."""
    service = ExternalServiceConfig(
        institution_id=test_mfi_institution.id,
        service_type=ServiceType.SCORECARD.value,
        service_name="Test Scorecard Service",
        service_provider="Test Provider",
        api_url="http://localhost:8001",
        timeout_seconds=30,
        is_primary=True,
        config_parameters={
            "score_threshold": 600,
            "grade_mapping": {
                "AA": [900, 1000],
                "A": [800, 899],
                "B": [700, 799],
                "C": [600, 699],
                "D": [0, 599]
            }
        },
        created_by_id=admin_user.id
    )
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    return service

# Edge case data fixtures
@pytest.fixture
def edge_case_generator():
    """Edge case data generator."""
    return EdgeCaseDataGenerator()

@pytest.fixture
def low_income_profile(edge_case_generator):
    """Low income customer profile."""
    return edge_case_generator.generate_low_income_profile()

@pytest.fixture
def missing_id_profile(edge_case_generator):
    """Missing ID customer profile."""
    return edge_case_generator.generate_missing_id_profile()

@pytest.fixture
def invalid_age_profile(edge_case_generator):
    """Invalid age customer profile."""
    return edge_case_generator.generate_invalid_age_profile("too_young")

@pytest.fixture
def high_debt_profile(edge_case_generator):
    """High debt customer profile."""
    return edge_case_generator.generate_high_debt_profile()

@pytest.fixture
def perfect_profile(edge_case_generator):
    """Perfect customer profile."""
    return edge_case_generator.generate_perfect_profile()

@pytest.fixture
def malformed_ocr_scenarios(edge_case_generator):
    """Malformed OCR test scenarios."""
    return edge_case_generator.generate_malformed_ocr_scenarios()

@pytest.fixture(scope="session")
def edge_case_dataset():
    """Complete edge case dataset."""
    return create_edge_case_dataset(10)

# Test data cleanup
@pytest.fixture(autouse=True)
async def cleanup_test_data(db_session: AsyncSession):
    """Clean up test data after each test."""
    yield
    # Cleanup happens automatically with test_db fixture