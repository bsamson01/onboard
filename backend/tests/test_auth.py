import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, patch

from app.models.user import User, UserRole
from app.core.auth import (
    create_access_token, verify_token, authenticate_user,
    get_current_user, require_role, require_admin
)
from app.services.audit_service import AuditService

class TestAuthentication:
    """Test authentication and authorization functionality."""

    @pytest.mark.asyncio
    async def test_user_registration_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test successful user registration."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data

    @pytest.mark.asyncio 
    async def test_user_registration_duplicate_email(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test registration with duplicate email."""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "password123",
            "first_name": "User",
            "last_name": "One"
        }
        
        # First registration
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Second registration with same email
        user_data["username"] = "user2"
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test successful user login."""
        # Create user first
        user_data = {
            "email": "login@example.com",
            "username": "loginuser",
            "password": "loginpassword123",
            "first_name": "Login",
            "last_name": "User"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Login
        login_data = {
            "username": "login@example.com",
            "password": "loginpassword123"
        }
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_account_locked(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test login attempt on locked account."""
        # Create user
        user_data = {
            "email": "locked@example.com",
            "username": "lockeduser", 
            "password": "password123",
            "first_name": "Locked",
            "last_name": "User"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Simulate failed login attempts to lock account
        login_data = {
            "username": "locked@example.com",
            "password": "wrongpassword"
        }
        
        # Attempt 5 failed logins to trigger lock
        for _ in range(5):
            await async_client.post("/api/v1/auth/login", data=login_data)
        
        # Now try with correct password - should still be locked
        login_data["password"] = "password123"
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "locked" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_token_refresh(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test token refresh functionality."""
        # Create and login user
        user_data = {
            "email": "refresh@example.com",
            "username": "refreshuser",
            "password": "password123",
            "first_name": "Refresh",
            "last_name": "User"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": "refresh@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Refresh token
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.post("/api/v1/auth/refresh", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_password_change(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test password change functionality."""
        # Create and login user
        user_data = {
            "email": "changepass@example.com",
            "username": "changepassuser",
            "password": "oldpassword123",
            "first_name": "Change",
            "last_name": "Password"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": "changepass@example.com",
            "password": "oldpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Change password
        headers = {"Authorization": f"Bearer {token}"}
        change_data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword123"
        }
        response = await async_client.post("/api/v1/auth/change-password", 
                                          json=change_data, headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_current_user(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting current user information."""
        # Create and login user
        user_data = {
            "email": "current@example.com",
            "username": "currentuser",
            "password": "password123",
            "first_name": "Current",
            "last_name": "User"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": "current@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]

class TestRoleBasedAccess:
    """Test role-based access control."""

    @pytest.mark.asyncio
    async def test_admin_role_enforcement(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test admin role enforcement on protected endpoints."""
        # Create regular user
        user_data = {
            "email": "regular@example.com",
            "username": "regularuser",
            "password": "password123",
            "first_name": "Regular",
            "last_name": "User"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": "regular@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Try to access admin endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.get("/api/v1/admin/dashboard", headers=headers)
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_multiple_role_access(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test endpoints that allow multiple roles."""
        # This would test endpoints that allow risk_officer OR loan_officer access
        # Implementation depends on specific endpoints
        pass

    @pytest.mark.asyncio
    async def test_role_inheritance(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that admin can access lower-privilege endpoints."""
        # Create admin user - this would require manually setting role in database
        # or having a special admin registration endpoint
        pass

class TestSecurityLogging:
    """Test security event logging."""

    @pytest.mark.asyncio
    async def test_login_success_logged(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that successful logins are logged."""
        with patch('app.core.logging.log_security_event') as mock_log:
            user_data = {
                "email": "logtest@example.com",
                "username": "loguser",
                "password": "password123",
                "first_name": "Log",
                "last_name": "User"
            }
            await async_client.post("/api/v1/auth/register", json=user_data)
            
            await async_client.post("/api/v1/auth/login", data={
                "username": "logtest@example.com",
                "password": "password123"
            })
            
            # Verify security event was logged
            mock_log.assert_called()
            call_args = mock_log.call_args
            assert call_args[0][0] == "login_success"

    @pytest.mark.asyncio
    async def test_login_failure_logged(self, async_client: AsyncClient):
        """Test that failed logins are logged."""
        with patch('app.core.logging.log_security_event') as mock_log:
            await async_client.post("/api/v1/auth/login", data={
                "username": "nonexistent@example.com",
                "password": "wrongpassword"
            })
            
            # Verify security event was logged
            mock_log.assert_called()
            call_args = mock_log.call_args
            assert call_args[0][0] == "login_failed"

    @pytest.mark.asyncio
    async def test_suspicious_activity_logged(self, async_client: AsyncClient):
        """Test that suspicious activities are logged."""
        with patch('app.core.logging.log_security_event') as mock_log:
            # Attempt multiple failed logins (suspicious behavior)
            for _ in range(3):
                await async_client.post("/api/v1/auth/login", data={
                    "username": "target@example.com",
                    "password": "wrongpassword"
                })
            
            # Should have logged multiple failed attempts
            assert mock_log.call_count >= 3

class TestAuditTrail:
    """Test audit trail functionality."""

    @pytest.mark.asyncio
    async def test_user_creation_audited(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that user creation is audited."""
        with patch.object(AuditService, 'log_onboarding_action') as mock_audit:
            user_data = {
                "email": "audit@example.com",
                "username": "audituser",
                "password": "password123",
                "first_name": "Audit",
                "last_name": "User"
            }
            await async_client.post("/api/v1/auth/register", json=user_data)
            
            # Verify audit log was created
            mock_audit.assert_called()

    @pytest.mark.asyncio
    async def test_password_change_audited(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that password changes are audited."""
        # Similar to password change test but with audit verification
        pass

class TestTokenValidation:
    """Test JWT token validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)

    def test_verify_valid_token(self):
        """Test verification of valid token."""
        data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"

    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        assert payload is None

    def test_verify_expired_token(self):
        """Test verification of expired token."""
        from datetime import datetime, timedelta
        
        # Create token that's already expired
        data = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() - timedelta(minutes=1)
        }
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        payload = verify_token(token)
        assert payload is None

class TestSessionManagement:
    """Test session management functionality."""

    @pytest.mark.asyncio
    async def test_session_tracking(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that user sessions are properly tracked."""
        # Create and login user
        user_data = {
            "email": "session@example.com",
            "username": "sessionuser",
            "password": "password123",
            "first_name": "Session",
            "last_name": "User"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": "session@example.com",
            "password": "password123"
        })
        
        # Verify session was created (would need to check database)
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_session_expiry(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that expired sessions are handled properly."""
        # This would test JWT expiration handling
        pass

    @pytest.mark.asyncio
    async def test_logout_session_cleanup(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that logout properly cleans up sessions."""
        # Create and login user
        user_data = {
            "email": "logout@example.com",
            "username": "logoutuser",
            "password": "password123",
            "first_name": "Logout",
            "last_name": "User"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": "logout@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200