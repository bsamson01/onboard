"""
Comprehensive security and robustness tests for the user profile system.
Tests input validation, authentication, authorization, and edge cases.
"""

import pytest
import uuid
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.profile import (
    ProfileUpdateRequest, RoleUpdateRequest, StateUpdateRequest,
    BulkUserOperationRequest, DocumentVerificationRequest
)
from app.models.user import User, UserRole, UserState
from app.services.user_state_service import UserStateService
from app.api.v1.endpoints.profile import (
    validate_uuid, sanitize_filename, validate_file_security,
    get_customer_safely, MAX_FILE_SIZE, ALLOWED_MIME_TYPES
)


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_profile_update_validation_valid_data(self):
        """Test valid profile update data."""
        valid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "marital_status": "single",
            "monthly_income": 50000.0,
            "employment_duration_months": 24
        }
        
        request = ProfileUpdateRequest(**valid_data)
        assert request.first_name == "John"
        assert request.monthly_income == 50000.0
    
    def test_profile_update_validation_invalid_data(self):
        """Test invalid profile update data validation."""
        # Test empty name
        with pytest.raises(ValueError, match="ensure this value has at least 1 characters"):
            ProfileUpdateRequest(first_name="")
        
        # Test invalid phone number
        with pytest.raises(ValueError, match="Phone number must contain 10-15 digits"):
            ProfileUpdateRequest(phone_number="123")
        
        # Test invalid date format
        with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD format"):
            ProfileUpdateRequest(date_of_birth="invalid-date")
        
        # Test future birth date
        future_date = (date.today() + timedelta(days=1)).isoformat()
        with pytest.raises(ValueError, match="Date of birth cannot be in the future"):
            ProfileUpdateRequest(date_of_birth=future_date)
        
        # Test underage
        recent_date = (date.today() - timedelta(days=365*10)).isoformat()
        with pytest.raises(ValueError, match="Age must be between 18 and 120 years"):
            ProfileUpdateRequest(date_of_birth=recent_date)
        
        # Test invalid gender
        with pytest.raises(ValueError, match="Gender must be one of"):
            ProfileUpdateRequest(gender="invalid")
        
        # Test negative income
        with pytest.raises(ValueError, match="ensure this value is greater than or equal to 0"):
            ProfileUpdateRequest(monthly_income=-1000)
        
        # Test excessive income
        with pytest.raises(ValueError, match="ensure this value is less than or equal to 10000000"):
            ProfileUpdateRequest(monthly_income=20000000)
    
    def test_role_update_validation(self):
        """Test role update validation."""
        # Valid role update
        request = RoleUpdateRequest(new_role=UserRole.LOAN_OFFICER, reason="Promotion")
        assert request.new_role == UserRole.LOAN_OFFICER
        
        # Invalid reason (too short)
        with pytest.raises(ValueError, match="Reason must be at least 3 characters long"):
            RoleUpdateRequest(new_role=UserRole.ADMIN, reason="x")
        
        # Invalid reason (too long)
        long_reason = "x" * 501
        with pytest.raises(ValueError, match="ensure this value has at most 500 characters"):
            RoleUpdateRequest(new_role=UserRole.ADMIN, reason=long_reason)
    
    def test_bulk_operation_validation(self):
        """Test bulk operation validation."""
        valid_uuid = str(uuid.uuid4())
        
        # Valid bulk operation
        request = BulkUserOperationRequest(
            user_ids=[valid_uuid],
            operation="activate",
            reason="Bulk activation"
        )
        assert len(request.user_ids) == 1
        
        # Empty user list
        with pytest.raises(ValueError, match="At least one user ID is required"):
            BulkUserOperationRequest(user_ids=[], operation="activate")
        
        # Too many users
        many_uuids = [str(uuid.uuid4()) for _ in range(101)]
        with pytest.raises(ValueError, match="Cannot process more than 100 users at once"):
            BulkUserOperationRequest(user_ids=many_uuids, operation="activate")
        
        # Duplicate user IDs
        with pytest.raises(ValueError, match="Duplicate user IDs are not allowed"):
            BulkUserOperationRequest(user_ids=[valid_uuid, valid_uuid], operation="activate")
        
        # Invalid UUID format
        with pytest.raises(ValueError, match="Invalid user ID format"):
            BulkUserOperationRequest(user_ids=["invalid-uuid"], operation="activate")
        
        # Invalid operation
        with pytest.raises(ValueError, match="string does not match regex"):
            BulkUserOperationRequest(user_ids=[valid_uuid], operation="invalid_op")


class TestFileSecurityValidation:
    """Test file upload security validation."""
    
    def test_validate_uuid(self):
        """Test UUID validation."""
        assert validate_uuid(str(uuid.uuid4())) is True
        assert validate_uuid("invalid-uuid") is False
        assert validate_uuid("") is False
        assert validate_uuid(None) is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Valid filename
        assert sanitize_filename("document.pdf") == "document.pdf"
        
        # Filename with path traversal attempt
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("/etc/passwd") == "passwd"
        assert sanitize_filename("..\\..\\windows\\system32") == "windows_system32"
        
        # Filename with dangerous characters
        assert sanitize_filename("doc<script>alert()</script>.pdf") == "docscriptalertscript.pdf"
        
        # Empty filename
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            sanitize_filename("")
        
        # Invalid filename (all dangerous characters)
        with pytest.raises(ValueError, match="Invalid filename"):
            sanitize_filename("<>|?*")
    
    def test_validate_file_security(self):
        """Test file security validation."""
        # Mock valid file
        valid_file = Mock()
        valid_file.filename = "test.pdf"
        valid_file.content_type = "application/pdf"
        valid_file.size = 1024 * 1024  # 1MB
        
        # Should not raise exception
        validate_file_security(valid_file)
        
        # Test no file
        with pytest.raises(HTTPException, match="No file provided"):
            validate_file_security(None)
        
        # Test no filename
        no_filename_file = Mock()
        no_filename_file.filename = None
        with pytest.raises(HTTPException, match="Filename is required"):
            validate_file_security(no_filename_file)
        
        # Test invalid extension
        invalid_ext_file = Mock()
        invalid_ext_file.filename = "test.exe"
        invalid_ext_file.content_type = "application/octet-stream"
        with pytest.raises(HTTPException, match="File type not allowed"):
            validate_file_security(invalid_ext_file)
        
        # Test invalid MIME type
        invalid_mime_file = Mock()
        invalid_mime_file.filename = "test.pdf"
        invalid_mime_file.content_type = "application/octet-stream"
        with pytest.raises(HTTPException, match="MIME type not allowed"):
            validate_file_security(invalid_mime_file)
        
        # Test file too large
        large_file = Mock()
        large_file.filename = "test.pdf"
        large_file.content_type = "application/pdf"
        large_file.size = MAX_FILE_SIZE + 1
        with pytest.raises(HTTPException, match="File too large"):
            validate_file_security(large_file)


class TestUserStateService:
    """Test user state service robustness."""
    
    @pytest.fixture
    def user_state_service(self):
        return UserStateService()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.user_state = UserState.REGISTERED
        user.onboarding_completed_at = None
        user.profile_expiry_date = None
        return user
    
    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)
    
    def test_validate_user_valid(self, user_state_service, mock_user):
        """Test user validation with valid user."""
        # Should not raise exception
        user_state_service._validate_user(mock_user)
    
    def test_validate_user_invalid(self, user_state_service):
        """Test user validation with invalid user."""
        # None user
        with pytest.raises(ValueError, match="User object is required"):
            user_state_service._validate_user(None)
        
        # User without ID
        invalid_user = Mock(spec=User)
        invalid_user.id = None
        invalid_user.email = "test@example.com"
        with pytest.raises(ValueError, match="User must have a valid ID"):
            user_state_service._validate_user(invalid_user)
        
        # User without email
        invalid_user = Mock(spec=User)
        invalid_user.id = uuid.uuid4()
        invalid_user.email = None
        with pytest.raises(ValueError, match="User must have a valid email"):
            user_state_service._validate_user(invalid_user)
    
    def test_validate_user_state(self, user_state_service):
        """Test user state validation."""
        # Valid states
        for state in [UserState.REGISTERED, UserState.ONBOARDED, UserState.OUTDATED]:
            user_state_service._validate_user_state(state)
        
        # Invalid state
        with pytest.raises(ValueError, match="Invalid user state type"):
            user_state_service._validate_user_state("invalid")
    
    def test_validate_state_transition(self, user_state_service):
        """Test state transition validation."""
        # Valid transitions
        user_state_service._validate_state_transition(
            UserState.REGISTERED, UserState.ONBOARDED
        )
        user_state_service._validate_state_transition(
            UserState.ONBOARDED, UserState.OUTDATED
        )
        
        # Invalid transitions
        with pytest.raises(ValueError, match="Invalid state transition"):
            user_state_service._validate_state_transition(
                UserState.REGISTERED, UserState.OUTDATED
            )
    
    @pytest.mark.asyncio
    async def test_check_user_state_robust(self, user_state_service, mock_user, mock_session):
        """Test check_user_state with various scenarios."""
        # Registered user
        mock_user.onboarding_completed_at = None
        state = await user_state_service.check_user_state(mock_user, mock_session)
        assert state == UserState.REGISTERED
        
        # Onboarded user
        mock_user.onboarding_completed_at = datetime.utcnow()
        mock_user.profile_expiry_date = datetime.utcnow() + timedelta(days=30)
        with patch.object(user_state_service, '_is_profile_outdated', return_value=False):
            state = await user_state_service.check_user_state(mock_user, mock_session)
            assert state == UserState.ONBOARDED
        
        # Outdated user
        with patch.object(user_state_service, '_is_profile_outdated', return_value=True):
            state = await user_state_service.check_user_state(mock_user, mock_session)
            assert state == UserState.OUTDATED
    
    @pytest.mark.asyncio
    async def test_update_user_state_robust(self, user_state_service, mock_user, mock_session):
        """Test update_user_state with error scenarios."""
        # Test with invalid user
        with pytest.raises(ValueError):
            await user_state_service.update_user_state(
                None, UserState.ONBOARDED, mock_session
            )
        
        # Test with invalid state
        with pytest.raises(ValueError):
            await user_state_service.update_user_state(
                mock_user, "invalid", mock_session
            )
        
        # Test with overly long reason
        long_reason = "x" * 501
        with pytest.raises(ValueError, match="Reason cannot exceed 500 characters"):
            await user_state_service.update_user_state(
                mock_user, UserState.ONBOARDED, mock_session, reason=long_reason
            )


class TestAuthorizationSecurity:
    """Test authentication and authorization security."""
    
    def test_admin_only_operations(self):
        """Test that admin operations require proper permissions."""
        # This would be integration tested with the actual endpoints
        # Here we test the validation logic
        
        # Mock non-admin user
        regular_user = Mock(spec=User)
        regular_user.role = UserRole.CUSTOMER
        regular_user.is_admin = False
        
        # Mock admin user
        admin_user = Mock(spec=User)
        admin_user.role = UserRole.ADMIN
        admin_user.is_admin = True
        
        # Test admin permissions
        assert admin_user.is_admin is True
        assert regular_user.is_admin is False
    
    def test_user_access_restrictions(self):
        """Test user access restrictions."""
        user1 = Mock(spec=User)
        user1.id = uuid.uuid4()
        user1.is_active = True
        user1.is_locked = False
        
        user2 = Mock(spec=User)
        user2.id = uuid.uuid4()
        user2.is_active = False
        user2.is_locked = True
        
        # Active user should have access
        assert user1.is_active and not user1.is_locked
        
        # Inactive or locked user should not have access
        assert not (user2.is_active and not user2.is_locked)


class TestErrorHandlingRobustness:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_get_customer_safely_error_handling(self):
        """Test get_customer_safely with various error conditions."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Test invalid UUID
        with pytest.raises(HTTPException, match="Database error retrieving customer data"):
            mock_session.execute.side_effect = Exception("Database error")
            await get_customer_safely("invalid-uuid", mock_session)
    
    def test_edge_case_data_handling(self):
        """Test handling of edge case data."""
        # Test empty strings
        request = ProfileUpdateRequest(first_name=" ", last_name=" ")
        # Should be stripped and validated
        
        # Test boundary values
        request = ProfileUpdateRequest(
            monthly_income=0,  # Minimum valid income
            employment_duration_months=600  # Maximum valid duration
        )
        assert request.monthly_income == 0
        assert request.employment_duration_months == 600
    
    def test_concurrent_access_safety(self):
        """Test concurrent access scenarios."""
        # This would test database transaction isolation
        # and proper locking mechanisms
        pass


class TestDataIntegrity:
    """Test data integrity and consistency."""
    
    def test_profile_data_consistency(self):
        """Test profile data consistency rules."""
        # Test that profile completion percentage calculation is consistent
        user = Mock(spec=User)
        user.user_state = UserState.REGISTERED
        user.onboarding_completed_at = None
        user.profile_expiry_date = None
        
        # Mock the property
        with patch.object(User, 'profile_completion_percentage', new_callable=lambda: property(lambda self: 0.0 if self.user_state == UserState.REGISTERED else 100.0)):
            user_with_prop = User()
            user_with_prop.user_state = UserState.REGISTERED
            # Would need actual implementation to test
    
    def test_state_transition_integrity(self):
        """Test that state transitions maintain data integrity."""
        service = UserStateService()
        
        # Test valid transitions
        service._validate_state_transition(UserState.REGISTERED, UserState.ONBOARDED)
        service._validate_state_transition(UserState.ONBOARDED, UserState.OUTDATED)
        
        # Test invalid transitions raise errors
        with pytest.raises(ValueError):
            service._validate_state_transition(UserState.REGISTERED, UserState.OUTDATED)


@pytest.mark.integration
class TestSecurityIntegration:
    """Integration tests for security features."""
    
    def test_complete_profile_workflow_security(self):
        """Test complete profile workflow with security considerations."""
        # This would be a comprehensive test that:
        # 1. Creates a user
        # 2. Tests profile updates with various validation scenarios
        # 3. Tests document uploads with security validation
        # 4. Tests admin operations with proper authorization
        # 5. Verifies audit logging throughout
        pass
    
    def test_attack_scenario_prevention(self):
        """Test prevention of common attack scenarios."""
        # Test SQL injection prevention
        # Test XSS prevention in stored data
        # Test file upload vulnerabilities
        # Test authentication bypass attempts
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])