import pytest
import hashlib
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit_service import AuditService
from app.models.user import AuditLog


@pytest.mark.asyncio
class TestAuditService:
    """Test audit service functionality."""
    
    @pytest.fixture
    def audit_service(self):
        """Create audit service instance."""
        return AuditService()
    
    async def test_log_onboarding_action_success(self, audit_service, test_db: AsyncSession):
        """Test successful audit log creation."""
        user_id = "user123"
        action = "test_action"
        resource_type = "test_resource"
        resource_id = "resource123"
        old_values = {"field1": "old_value"}
        new_values = {"field1": "new_value"}
        ip_address = "192.168.1.1"
        user_agent = "test-agent"
        additional_data = {"context": "test"}
        
        result = await audit_service.log_onboarding_action(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=additional_data,
            session=test_db
        )
        
        assert result is True
        
        # Verify audit log was created
        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.action == action)
        audit_log = (await test_db.execute(stmt)).scalar()
        
        assert audit_log is not None
        assert audit_log.user_id == user_id
        assert audit_log.action == action
        assert audit_log.resource_type == resource_type
        assert audit_log.resource_id == resource_id
        assert audit_log.ip_address == ip_address
        assert audit_log.user_agent == user_agent
    
    async def test_log_onboarding_action_without_session(self, audit_service, monkeypatch):
        """Test audit logging without providing session."""
        mock_session = AsyncMock()
        mock_get_session = AsyncMock()
        mock_get_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_get_session.__aexit__ = AsyncMock(return_value=None)
        
        monkeypatch.setattr("app.services.audit_service.get_async_db", lambda: mock_get_session)
        
        with patch.object(audit_service, '_write_audit_log', return_value=True) as mock_write:
            result = await audit_service.log_onboarding_action(
                user_id="user123",
                action="test_action",
                resource_type="test_resource",
                resource_id="resource123"
            )
            
            assert result is True
            mock_write.assert_called_once()
    
    def test_sanitize_sensitive_data(self, audit_service):
        """Test sensitive data sanitization."""
        sensitive_data = {
            "password": "secret123",
            "hashed_password": "hash123",
            "bank_account_number": "1234567890",
            "id_number": "ID987654321",
            "passport_number": "P123456789",
            "safe_field": "safe_value",
            "nested": {
                "password": "nested_secret",
                "safe_nested": "safe_value"
            },
            "list_data": [
                {"password": "list_secret", "safe": "value"},
                "safe_string"
            ]
        }
        
        sanitized = audit_service._sanitize_sensitive_data(sensitive_data)
        
        # Check sensitive fields are masked
        assert sanitized["password"] == "***"
        assert sanitized["hashed_password"] == "***"
        assert sanitized["bank_account_number"] == "***7890"  # Last 4 chars
        assert sanitized["id_number"] == "***4321"
        assert sanitized["passport_number"] == "***6789"
        
        # Check safe fields are preserved
        assert sanitized["safe_field"] == "safe_value"
        
        # Check nested sanitization
        assert sanitized["nested"]["password"] == "***"
        assert sanitized["nested"]["safe_nested"] == "safe_value"
        
        # Check list sanitization
        assert sanitized["list_data"][0]["password"] == "***"
        assert sanitized["list_data"][0]["safe"] == "value"
        assert sanitized["list_data"][1] == "safe_string"
    
    def test_sanitize_sensitive_data_empty(self, audit_service):
        """Test sanitization with empty data."""
        assert audit_service._sanitize_sensitive_data(None) is None
        assert audit_service._sanitize_sensitive_data({}) == {}
    
    def test_create_consent_fingerprint(self, audit_service):
        """Test consent fingerprint creation."""
        consent_data = {
            "consent_data_processing": True,
            "consent_credit_check": True,
            "timestamp": "2024-01-01T00:00:00"
        }
        ip_address = "192.168.1.1"
        user_agent = "test-agent"
        
        # Mock datetime to get consistent results
        with patch('app.services.audit_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T00:00:00"
            
            fingerprint = audit_service._create_consent_fingerprint(
                consent_data, ip_address, user_agent
            )
            
            assert isinstance(fingerprint, str)
            assert len(fingerprint) == 64  # SHA-256 hex digest length
            
            # Verify reproducible
            fingerprint2 = audit_service._create_consent_fingerprint(
                consent_data, ip_address, user_agent
            )
            assert fingerprint == fingerprint2
            
            # Verify changes with different data
            different_data = consent_data.copy()
            different_data["consent_marketing"] = True
            fingerprint3 = audit_service._create_consent_fingerprint(
                different_data, ip_address, user_agent
            )
            assert fingerprint != fingerprint3
    
    async def test_log_application_created(self, audit_service):
        """Test logging application creation."""
        with patch.object(audit_service, 'log_onboarding_action', return_value=True) as mock_log:
            await audit_service.log_application_created(
                user_id="user123",
                application_id="app123",
                application_data={"step": 1},
                ip_address="192.168.1.1",
                user_agent="test-agent"
            )
            
            mock_log.assert_called_once_with(
                user_id="user123",
                action="onboarding_application_created",
                resource_type="onboarding_application",
                resource_id="app123",
                old_values=None,
                new_values={"step": 1},
                ip_address="192.168.1.1",
                user_agent="test-agent",
                additional_data={"step": "application_creation"}
            )
    
    async def test_log_step_completed(self, audit_service):
        """Test logging step completion."""
        with patch.object(audit_service, 'log_onboarding_action', return_value=True) as mock_log:
            await audit_service.log_step_completed(
                user_id="user123",
                application_id="app123",
                step_number=2,
                step_name="Personal Info",
                step_data={"name": "John"},
                ip_address="192.168.1.1",
                user_agent="test-agent"
            )
            
            mock_log.assert_called_once_with(
                user_id="user123",
                action="onboarding_step_completed",
                resource_type="onboarding_step",
                resource_id="app123:step_2",
                old_values=None,
                new_values={"name": "John"},
                ip_address="192.168.1.1",
                user_agent="test-agent",
                additional_data={
                    "application_id": "app123",
                    "step_number": 2,
                    "step_name": "Personal Info"
                }
            )
    
    async def test_log_document_uploaded(self, audit_service):
        """Test logging document upload."""
        with patch.object(audit_service, 'log_onboarding_action', return_value=True) as mock_log:
            await audit_service.log_document_uploaded(
                user_id="user123",
                application_id="app123",
                document_id="doc123",
                document_type="national_id",
                file_info={"filename": "id.jpg"},
                ip_address="192.168.1.1",
                user_agent="test-agent"
            )
            
            mock_log.assert_called_once_with(
                user_id="user123",
                action="document_uploaded",
                resource_type="document",
                resource_id="doc123",
                old_values=None,
                new_values={"filename": "id.jpg"},
                ip_address="192.168.1.1",
                user_agent="test-agent",
                additional_data={
                    "application_id": "app123",
                    "document_type": "national_id"
                }
            )
    
    async def test_log_ocr_processed(self, audit_service):
        """Test logging OCR processing."""
        with patch.object(audit_service, 'log_onboarding_action', return_value=True) as mock_log:
            await audit_service.log_ocr_processed(
                user_id="user123",
                document_id="doc123",
                ocr_results={"confidence": 85.5},
                ip_address="192.168.1.1"
            )
            
            mock_log.assert_called_once_with(
                user_id="user123",
                action="document_ocr_processed",
                resource_type="document",
                resource_id="doc123",
                old_values=None,
                new_values={"confidence": 85.5},
                ip_address="192.168.1.1",
                additional_data={"process_type": "ocr"}
            )
    
    async def test_log_score_calculated(self, audit_service):
        """Test logging score calculation."""
        with patch.object(audit_service, 'log_onboarding_action', return_value=True) as mock_log:
            await audit_service.log_score_calculated(
                user_id="user123",
                application_id="app123",
                score_results={"score": 720},
                ip_address="192.168.1.1"
            )
            
            mock_log.assert_called_once_with(
                user_id="user123",
                action="credit_score_calculated",
                resource_type="onboarding_application",
                resource_id="app123",
                old_values=None,
                new_values={"score": 720},
                ip_address="192.168.1.1",
                additional_data={"process_type": "scoring"}
            )
    
    async def test_log_consent_recorded(self, audit_service):
        """Test logging consent recording."""
        consent_data = {"consent_data_processing": True}
        
        with patch.object(audit_service, 'log_onboarding_action', return_value=True) as mock_log:
            with patch.object(audit_service, '_create_consent_fingerprint', return_value="fingerprint123") as mock_fingerprint:
                await audit_service.log_consent_recorded(
                    user_id="user123",
                    application_id="app123",
                    consent_data=consent_data,
                    ip_address="192.168.1.1",
                    user_agent="test-agent"
                )
                
                mock_fingerprint.assert_called_once_with(consent_data, "192.168.1.1", "test-agent")
                mock_log.assert_called_once()
                
                # Check additional_data contains fingerprint
                call_args = mock_log.call_args
                additional_data = call_args[1]["additional_data"]
                assert additional_data["consent_fingerprint"] == "fingerprint123"
                assert "consent_timestamp" in additional_data
    
    async def test_log_validation_error(self, audit_service):
        """Test logging validation errors."""
        errors = ["Field required", "Invalid format"]
        
        with patch.object(audit_service, 'log_onboarding_action', return_value=True) as mock_log:
            await audit_service.log_validation_error(
                user_id="user123",
                application_id="app123",
                step_number=2,
                validation_errors=errors,
                ip_address="192.168.1.1"
            )
            
            mock_log.assert_called_once_with(
                user_id="user123",
                action="validation_error",
                resource_type="onboarding_application",
                resource_id="app123",
                old_values=None,
                new_values={"errors": errors},
                ip_address="192.168.1.1",
                additional_data={
                    "step_number": 2,
                    "error_count": 2
                }
            )
    
    async def test_get_application_audit_trail(self, audit_service, test_db: AsyncSession):
        """Test getting application audit trail."""
        # Create test audit logs
        audit_logs = [
            AuditLog(
                user_id="user123",
                action="application_created",
                resource_type="onboarding_application",
                resource_id="app123",
                ip_address="192.168.1.1",
                additional_data={"step": "creation"}
            ),
            AuditLog(
                user_id="user123",
                action="step_completed",
                resource_type="onboarding_step",
                resource_id="app123",
                ip_address="192.168.1.1",
                additional_data={"step": 1}
            )
        ]
        
        for log in audit_logs:
            test_db.add(log)
        await test_db.commit()
        
        # Get audit trail
        trail = await audit_service.get_application_audit_trail("app123", test_db)
        
        assert len(trail) == 1  # Only application-level logs, not step logs
        assert trail[0]["action"] == "application_created"
        assert trail[0]["resource_type"] == "onboarding_application"
        assert trail[0]["resource_id"] == "app123"
        assert "id" in trail[0]
        assert "timestamp" in trail[0]
    
    async def test_error_handling(self, audit_service):
        """Test error handling in audit service."""
        # Test with invalid session
        mock_session = MagicMock()
        mock_session.add.side_effect = Exception("Database error")
        
        result = await audit_service._write_audit_log(
            session=mock_session,
            user_id="user123",
            action="test_action",
            resource_type="test_resource",
            resource_id="resource123",
            old_values=None,
            new_values=None,
            ip_address=None,
            user_agent=None,
            additional_data=None
        )
        
        assert result is False