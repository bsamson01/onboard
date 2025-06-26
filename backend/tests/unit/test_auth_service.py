import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    verify_token,
    get_current_user,
    authenticate_user,
    require_role,
    require_roles
)
from app.models.user import User, UserRole
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


class TestPasswordHandling:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert verify_password(password, hashed) is True
    
    def test_password_verification_invalid(self):
        """Test password verification with wrong password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_password_verification_empty(self):
        """Test password verification with empty password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token_default_expiry(self):
        """Test creating access token with default expiry."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Verify token content
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload
    
    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta)
        
        payload = verify_token(token)
        assert payload is not None
        
        # Check expiry is approximately correct (within 1 minute)
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + expires_delta
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    def test_verify_token_invalid(self):
        """Test verifying invalid token."""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        assert payload is None
    
    def test_verify_token_expired(self):
        """Test verifying expired token."""
        data = {"sub": "user123"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta)
        
        payload = verify_token(token)
        assert payload is None


@pytest.mark.asyncio
class TestUserAuthentication:
    """Test user authentication functions."""
    
    async def test_authenticate_user_success(self, test_db: AsyncSession):
        """Test successful user authentication."""
        # Create test user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER,
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
        
        # Authenticate
        authenticated_user = await authenticate_user(test_db, "test@example.com", "password123")
        
        assert authenticated_user is not None
        assert authenticated_user.email == "test@example.com"
        assert authenticated_user.failed_login_attempts == 0
        assert authenticated_user.last_login is not None
    
    async def test_authenticate_user_wrong_password(self, test_db: AsyncSession):
        """Test authentication with wrong password."""
        # Create test user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER,
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
        
        # Try to authenticate with wrong password
        authenticated_user = await authenticate_user(test_db, "test@example.com", "wrongpassword")
        
        assert authenticated_user is None
        
        # Check failed attempts incremented
        await test_db.refresh(user)
        assert user.failed_login_attempts == 1
    
    async def test_authenticate_user_nonexistent(self, test_db: AsyncSession):
        """Test authentication with non-existent user."""
        authenticated_user = await authenticate_user(test_db, "nonexistent@example.com", "password")
        assert authenticated_user is None
    
    async def test_authenticate_user_account_lockout(self, test_db: AsyncSession):
        """Test account lockout after multiple failed attempts."""
        # Create test user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER,
            is_active=True,
            failed_login_attempts=4  # One away from lockout
        )
        test_db.add(user)
        await test_db.commit()
        
        # Try to authenticate with wrong password (should trigger lockout)
        authenticated_user = await authenticate_user(test_db, "test@example.com", "wrongpassword")
        
        assert authenticated_user is None
        
        # Check account is locked
        await test_db.refresh(user)
        assert user.failed_login_attempts == 5
        assert user.is_locked is True


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Test getting current user from token."""
    
    async def test_get_current_user_success(self, test_db: AsyncSession):
        """Test getting current user with valid token."""
        # Create test user
        user = User(
            email="test@example.com",
            username="testuser", 
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER,
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
        
        # Create token
        token = create_access_token(data={"sub": str(user.id)})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Get current user
        current_user = await get_current_user(credentials, test_db)
        
        assert current_user is not None
        assert current_user.id == user.id
        assert current_user.email == "test@example.com"
    
    async def test_get_current_user_invalid_token(self, test_db: AsyncSession):
        """Test getting current user with invalid token."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, test_db)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
    
    async def test_get_current_user_inactive_user(self, test_db: AsyncSession):
        """Test getting current user when user is inactive."""
        # Create inactive user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER,
            is_active=False  # Inactive user
        )
        test_db.add(user)
        await test_db.commit()
        
        token = create_access_token(data={"sub": str(user.id)})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, test_db)
        
        assert exc_info.value.status_code == 403
        assert "User account is deactivated" in exc_info.value.detail
    
    async def test_get_current_user_locked_user(self, test_db: AsyncSession):
        """Test getting current user when user is locked."""
        # Create locked user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER,
            is_active=True,
            is_locked=True  # Locked user
        )
        test_db.add(user)
        await test_db.commit()
        
        token = create_access_token(data={"sub": str(user.id)})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, test_db)
        
        assert exc_info.value.status_code == 423
        assert "User account is locked" in exc_info.value.detail


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    def test_require_role_success(self):
        """Test role requirement with correct role."""
        user = User(role=UserRole.ADMIN)
        role_dependency = require_role("admin")
        
        # Should not raise exception
        result = role_dependency(user)
        assert result == user
    
    def test_require_role_failure(self):
        """Test role requirement with incorrect role."""
        user = User(role=UserRole.CUSTOMER)
        role_dependency = require_role("admin")
        
        with pytest.raises(HTTPException) as exc_info:
            role_dependency(user)
        
        assert exc_info.value.status_code == 403
        assert "Required role: admin" in exc_info.value.detail
    
    def test_require_roles_success(self):
        """Test multiple role requirement with one matching role."""
        user = User(role=UserRole.LOAN_OFFICER)
        roles_dependency = require_roles(["admin", "loan_officer"])
        
        # Should not raise exception
        result = roles_dependency(user)
        assert result == user
    
    def test_require_roles_failure(self):
        """Test multiple role requirement with no matching roles."""
        user = User(role=UserRole.CUSTOMER)
        roles_dependency = require_roles(["admin", "loan_officer"])
        
        with pytest.raises(HTTPException) as exc_info:
            roles_dependency(user)
        
        assert exc_info.value.status_code == 403
        assert "Required roles: admin, loan_officer" in exc_info.value.detail


class TestRoleProperties:
    """Test user role property methods."""
    
    def test_admin_properties(self):
        """Test admin user properties."""
        admin_user = User(role=UserRole.ADMIN)
        
        assert admin_user.is_admin is True
        assert admin_user.can_access_admin is True
        assert admin_user.can_access_risk is True
        assert admin_user.can_access_loans is True
    
    def test_risk_officer_properties(self):
        """Test risk officer user properties."""
        risk_user = User(role=UserRole.RISK_OFFICER)
        
        assert risk_user.is_risk_officer is True
        assert risk_user.can_access_admin is False
        assert risk_user.can_access_risk is True
        assert risk_user.can_access_loans is True
    
    def test_loan_officer_properties(self):
        """Test loan officer user properties."""
        loan_user = User(role=UserRole.LOAN_OFFICER)
        
        assert loan_user.is_loan_officer is True
        assert loan_user.can_access_admin is False
        assert loan_user.can_access_risk is False
        assert loan_user.can_access_loans is True
    
    def test_customer_properties(self):
        """Test customer user properties."""
        customer = User(role=UserRole.CUSTOMER)
        
        assert customer.is_customer is True
        assert customer.can_access_admin is False
        assert customer.can_access_risk is False
        assert customer.can_access_loans is False