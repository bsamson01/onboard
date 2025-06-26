import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
import tempfile
import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import httpx

from app.main import app
from app.database import Base, get_async_session
from app.models.user import User, UserRole
from app.models.onboarding import Customer, OnboardingApplication
from app.config import settings
from app.core.auth import get_password_hash, create_access_token


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[TestClient, None]:
    """Create a test client with database dependency override."""
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_async_session] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        first_name="Test",
        last_name="User",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def admin_user(test_db: AsyncSession) -> User:
    """Create an admin test user."""
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("adminpassword"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authorization headers for test user."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict:
    """Create authorization headers for admin user."""
    token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_customer(test_db: AsyncSession, test_user: User) -> Customer:
    """Create a test customer."""
    customer = Customer(
        user_id=test_user.id,
        customer_number="CUST001",
        date_of_birth="1990-01-01",
        gender="male",
        nationality="US",
        id_number="ID123456789"
    )
    test_db.add(customer)
    await test_db.commit()
    await test_db.refresh(customer)
    return customer


@pytest.fixture
async def test_application(test_db: AsyncSession, test_customer: Customer) -> OnboardingApplication:
    """Create a test onboarding application."""
    application = OnboardingApplication(
        customer_id=test_customer.id,
        application_number="APP001",
        current_step=1,
        total_steps=5
    )
    test_db.add(application)
    await test_db.commit()
    await test_db.refresh(application)
    return application


@pytest.fixture
def temp_upload_dir():
    """Create a temporary upload directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        old_upload_dir = settings.UPLOAD_DIR
        settings.UPLOAD_DIR = temp_dir
        yield temp_dir
        settings.UPLOAD_DIR = old_upload_dir


@pytest.fixture
def mock_file():
    """Create a mock file for testing uploads."""
    mock_file = MagicMock()
    mock_file.filename = "test_document.jpg"
    mock_file.content_type = "image/jpeg"
    mock_file.size = 1024
    mock_file.read = AsyncMock(return_value=b"fake file content")
    mock_file.seek = AsyncMock()
    return mock_file


@pytest.fixture
def mock_ocr_service():
    """Mock OCR service for testing."""
    mock = MagicMock()
    mock.process_document = AsyncMock(return_value={
        'ocr_text': 'Sample OCR text',
        'extracted_data': {
            'id_number': '123456789',
            'full_name': 'John Doe',
            'date_of_birth': '1990-01-01'
        },
        'confidence': 85.5,
        'processing_status': 'completed'
    })
    mock.validate_document_quality = AsyncMock(return_value={
        'valid': True,
        'reason': 'Document quality acceptable'
    })
    return mock


@pytest.fixture
def mock_scorecard_service():
    """Mock scorecard service for testing."""
    mock = MagicMock()
    mock.calculate_score = AsyncMock(return_value=MagicMock(
        score=720,
        grade="A",
        eligibility="eligible",
        message="Good credit profile",
        breakdown={"base_score": 700, "adjustments": 20},
        recommendations=["Maintain good payment history"]
    ))
    mock.validate_scorecard_service = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_audit_service():
    """Mock audit service for testing."""
    mock = MagicMock()
    mock.log_onboarding_action = AsyncMock(return_value=True)
    mock.log_application_created = AsyncMock()
    mock.log_step_completed = AsyncMock()
    mock.log_document_uploaded = AsyncMock()
    mock.log_consent_recorded = AsyncMock()
    return mock


@pytest.fixture
def mock_file_service():
    """Mock file service for testing."""
    mock = MagicMock()
    mock.upload_document = AsyncMock(return_value={
        'id': 'file123',
        'filename': 'test_document.jpg',
        'file_path': '/uploads/test_document.jpg',
        'file_size': 1024,
        'mime_type': 'image/jpeg',
        'file_hash': 'abcd1234'
    })
    return mock


@pytest.fixture
async def mock_external_scorecard():
    """Mock external scorecard API responses."""
    async def mock_post(*args, **kwargs):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "customer_id": "test123",
            "score": 720,
            "credit_band": "A",
            "scorecard_version": "1.0",
            "breakdown": {
                "base_score": 700,
                "income_adjustment": 20,
                "final_score": 720
            }
        }
        return response
    
    async def mock_get(*args, **kwargs):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"status": "healthy", "service": "scorecard"}
        return response
    
    with httpx.AsyncClient() as client:
        client.post = mock_post
        client.get = mock_get
        yield client


# Test data factories
class UserFactory:
    """Factory for creating test users."""
    
    @staticmethod
    def build(**kwargs):
        defaults = {
            "email": "user@example.com",
            "username": "testuser",
            "hashed_password": get_password_hash("password"),
            "first_name": "Test",
            "last_name": "User",
            "role": UserRole.CUSTOMER,
            "is_active": True,
            "is_verified": True
        }
        defaults.update(kwargs)
        return User(**defaults)


class CustomerFactory:
    """Factory for creating test customers."""
    
    @staticmethod
    def build(user_id=None, **kwargs):
        defaults = {
            "user_id": user_id,
            "customer_number": "CUST001",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "nationality": "US",
            "id_number": "ID123456789"
        }
        defaults.update(kwargs)
        return Customer(**defaults)


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def customer_factory():
    return CustomerFactory