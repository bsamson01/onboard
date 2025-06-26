import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.core.auth import get_password_hash, create_access_token


@pytest.mark.integration
class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""
    
    async def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "testpassword123",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["first_name"] == user_data["first_name"]
        assert data["last_name"] == user_data["last_name"]
        assert "password" not in data
        assert "hashed_password" not in data
    
    async def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with duplicate email."""
        user_data = {
            "email": test_user.email,  # Same email as existing user
            "username": "uniqueusername",
            "password": "testpassword123",
            "first_name": "Duplicate",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    async def test_register_invalid_data(self, client: TestClient):
        """Test registration with invalid data."""
        user_data = {
            "email": "invalid-email",  # Invalid email format
            "username": "",  # Empty username
            "password": "123",  # Too short password
            "first_name": "",
            "last_name": ""
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["email"] == test_user.email
    
    async def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    async def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    async def test_login_inactive_user(self, client: TestClient, test_db: AsyncSession):
        """Test login with inactive user."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            username="inactive",
            hashed_password=get_password_hash("password"),
            first_name="Inactive",
            last_name="User",
            role=UserRole.CUSTOMER,
            is_active=False
        )
        test_db.add(inactive_user)
        await test_db.commit()
        
        login_data = {
            "username": "inactive@example.com",
            "password": "password"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Account is inactive" in response.json()["detail"]
    
    async def test_login_locked_user(self, client: TestClient, test_db: AsyncSession):
        """Test login with locked user."""
        # Create locked user
        locked_user = User(
            email="locked@example.com",
            username="locked",
            hashed_password=get_password_hash("password"),
            first_name="Locked",
            last_name="User",
            role=UserRole.CUSTOMER,
            is_active=True,
            is_locked=True
        )
        test_db.add(locked_user)
        await test_db.commit()
        
        login_data = {
            "username": "locked@example.com",
            "password": "password"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Account is locked" in response.json()["detail"]
    
    def test_refresh_token_success(self, client: TestClient, auth_headers: dict):
        """Test successful token refresh."""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
    
    def test_refresh_token_no_auth(self, client: TestClient):
        """Test token refresh without authentication."""
        response = client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 401
    
    def test_refresh_token_invalid_token(self, client: TestClient):
        """Test token refresh with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/v1/auth/refresh", headers=headers)
        
        assert response.status_code == 401
    
    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """Test successful logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully logged out" in data["message"]
    
    def test_logout_no_auth(self, client: TestClient):
        """Test logout without authentication."""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401
    
    def test_change_password_success(self, client: TestClient, auth_headers: dict):
        """Test successful password change."""
        password_data = {
            "current_password": "testpassword",
            "new_password": "newpassword123"
        }
        
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Password changed successfully" in data["message"]
    
    def test_change_password_wrong_current(self, client: TestClient, auth_headers: dict):
        """Test password change with wrong current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]
    
    def test_change_password_no_auth(self, client: TestClient):
        """Test password change without authentication."""
        password_data = {
            "current_password": "current",
            "new_password": "new"
        }
        
        response = client.post("/api/v1/auth/change-password", json=password_data)
        
        assert response.status_code == 401
    
    def test_verify_token_success(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test successful token verification."""
        response = client.get("/api/v1/auth/verify-token", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["role"] == test_user.role.value
    
    def test_verify_token_invalid(self, client: TestClient):
        """Test token verification with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/verify-token", headers=headers)
        
        assert response.status_code == 401
    
    def test_verify_token_no_auth(self, client: TestClient):
        """Test token verification without authentication."""
        response = client.get("/api/v1/auth/verify-token")
        
        assert response.status_code == 401


@pytest.mark.integration
class TestAuthSecurityFeatures:
    """Test security features of authentication."""
    
    async def test_account_lockout_after_failed_attempts(self, client: TestClient, test_db: AsyncSession):
        """Test account lockout after multiple failed login attempts."""
        # Create test user
        user = User(
            email="lockout@example.com",
            username="lockout",
            hashed_password=get_password_hash("correctpassword"),
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER,
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
        
        login_data = {
            "username": "lockout@example.com",
            "password": "wrongpassword"
        }
        
        # Try to login 5 times with wrong password
        for i in range(5):
            response = client.post("/api/v1/auth/login", data=login_data)
            assert response.status_code == 401
        
        # Account should now be locked
        await test_db.refresh(user)
        assert user.is_locked is True
        assert user.failed_login_attempts == 5
        
        # Try with correct password - should still fail due to lockout
        correct_login = {
            "username": "lockout@example.com",
            "password": "correctpassword"
        }
        response = client.post("/api/v1/auth/login", data=correct_login)
        assert response.status_code == 401
        assert "Account is locked" in response.json()["detail"]
    
    async def test_failed_attempts_reset_on_success(self, client: TestClient, test_db: AsyncSession):
        """Test that failed attempts are reset on successful login."""
        # Create test user with some failed attempts
        user = User(
            email="reset@example.com",
            username="reset",
            hashed_password=get_password_hash("correctpassword"),
            first_name="Test",
            last_name="User",
            role=UserRole.CUSTOMER,
            is_active=True,
            failed_login_attempts=3
        )
        test_db.add(user)
        await test_db.commit()
        
        # Login with correct password
        login_data = {
            "username": "reset@example.com",
            "password": "correctpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        # Failed attempts should be reset
        await test_db.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.last_login is not None
    
    def test_token_expiration_handling(self, client: TestClient, test_user: User):
        """Test handling of expired tokens."""
        from datetime import timedelta
        
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/verify-token", headers=headers)
        
        assert response.status_code == 401
    
    def test_malformed_token_handling(self, client: TestClient):
        """Test handling of malformed tokens."""
        malformed_tokens = [
            "invalid.token.format",
            "Bearer",
            "",
            "random_string",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
        ]
        
        for token in malformed_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/auth/verify-token", headers=headers)
            assert response.status_code == 401, f"Token should be rejected: {token}"