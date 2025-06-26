import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models.user import AuditLog
from app.database import AsyncDatabaseManager

logger = logging.getLogger(__name__)


class AuditService:
    """Service for immutable audit logging of all onboarding activities."""
    
    def __init__(self):
        """Initialize audit service."""
        self.logger = logging.getLogger("audit")
    
    async def log_onboarding_action(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        session: Optional[AsyncSession] = None
    ) -> bool:
        """
        Log an onboarding-related action to the audit trail.
        
        Args:
            user_id: ID of the user performing the action
            action: Description of the action performed
            resource_type: Type of resource being acted upon
            resource_id: ID of the specific resource
            old_values: Previous values before the action
            new_values: New values after the action
            ip_address: IP address of the user
            user_agent: User agent string
            additional_data: Any additional context data
            session: Database session to use
            
        Returns:
            True if logging successful, False otherwise
        """
        try:
            # Use provided session or create new one
            if session is None:
                async with AsyncDatabaseManager() as db_session:
                    return await self._write_audit_log(
                        db_session, user_id, action, resource_type, resource_id,
                        old_values, new_values, ip_address, user_agent, additional_data
                    )
            else:
                return await self._write_audit_log(
                    session, user_id, action, resource_type, resource_id,
                    old_values, new_values, ip_address, user_agent, additional_data
                )
                
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
            return False
    
    async def _write_audit_log(
        self,
        session: AsyncSession,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: str,
        old_values: Optional[Dict[str, Any]],
        new_values: Optional[Dict[str, Any]],
        ip_address: Optional[str],
        user_agent: Optional[str],
        additional_data: Optional[Dict[str, Any]]
    ) -> bool:
        """Write audit log entry to database."""
        try:
            # Sanitize values for logging
            safe_old_values = self._sanitize_sensitive_data(old_values) if old_values else None
            safe_new_values = self._sanitize_sensitive_data(new_values) if new_values else None
            safe_additional_data = self._sanitize_sensitive_data(additional_data) if additional_data else None
            
            # Create audit log entry
            audit_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=safe_old_values,
                new_values=safe_new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data=safe_additional_data
            )
            
            session.add(audit_entry)
            await session.commit()
            
            # Also log to application logger for immediate visibility
            self.logger.info(
                f"AUDIT: {action} | Resource: {resource_type}:{resource_id} | "
                f"User: {user_id} | IP: {ip_address}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write audit log entry: {str(e)}")
            await session.rollback()
            return False
    
    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask sensitive data from audit logs."""
        if not data:
            return data
        
        # List of sensitive field names to redact
        sensitive_fields = {
            'password', 'hashed_password', 'secret', 'token', 'api_key',
            'bank_account_number', 'id_number', 'passport_number',
            'social_security_number', 'credit_card_number'
        }
        
        sanitized = {}
        for key, value in data.items():
            if isinstance(key, str) and key.lower() in sensitive_fields:
                # Mask sensitive data
                if isinstance(value, str) and len(value) > 4:
                    sanitized[key] = f"***{value[-4:]}"  # Show last 4 characters
                else:
                    sanitized[key] = "***"
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self._sanitize_sensitive_data(value)
            elif isinstance(value, list):
                # Handle lists of dictionaries
                sanitized[key] = [
                    self._sanitize_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def log_application_created(
        self,
        user_id: str,
        application_id: str,
        application_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log creation of new onboarding application."""
        await self.log_onboarding_action(
            user_id=user_id,
            action="onboarding_application_created",
            resource_type="onboarding_application",
            resource_id=application_id,
            old_values=None,
            new_values=application_data,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data={"step": "application_creation"}
        )
    
    async def log_step_completed(
        self,
        user_id: str,
        application_id: str,
        step_number: int,
        step_name: str,
        step_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log completion of an onboarding step."""
        await self.log_onboarding_action(
            user_id=user_id,
            action="onboarding_step_completed",
            resource_type="onboarding_step",
            resource_id=f"{application_id}:step_{step_number}",
            old_values=None,
            new_values=step_data,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data={
                "application_id": application_id,
                "step_number": step_number,
                "step_name": step_name
            }
        )
    
    async def log_document_uploaded(
        self,
        user_id: str,
        application_id: str,
        document_id: str,
        document_type: str,
        file_info: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log document upload."""
        await self.log_onboarding_action(
            user_id=user_id,
            action="document_uploaded",
            resource_type="document",
            resource_id=document_id,
            old_values=None,
            new_values=file_info,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data={
                "application_id": application_id,
                "document_type": document_type
            }
        )
    
    async def log_ocr_processed(
        self,
        user_id: str,
        document_id: str,
        ocr_results: Dict[str, Any],
        ip_address: Optional[str] = None
    ):
        """Log OCR processing results."""
        await self.log_onboarding_action(
            user_id=user_id,
            action="document_ocr_processed",
            resource_type="document",
            resource_id=document_id,
            old_values=None,
            new_values=ocr_results,
            ip_address=ip_address,
            additional_data={"process_type": "ocr"}
        )
    
    async def log_score_calculated(
        self,
        user_id: str,
        application_id: str,
        score_results: Dict[str, Any],
        ip_address: Optional[str] = None
    ):
        """Log credit score calculation."""
        await self.log_onboarding_action(
            user_id=user_id,
            action="credit_score_calculated",
            resource_type="onboarding_application",
            resource_id=application_id,
            old_values=None,
            new_values=score_results,
            ip_address=ip_address,
            additional_data={"process_type": "scoring"}
        )
    
    async def log_consent_recorded(
        self,
        user_id: str,
        application_id: str,
        consent_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log consent recording with fingerprint."""
        # Create consent fingerprint for integrity verification
        consent_fingerprint = self._create_consent_fingerprint(consent_data, ip_address, user_agent)
        
        await self.log_onboarding_action(
            user_id=user_id,
            action="consent_recorded",
            resource_type="consent_record",
            resource_id=f"{application_id}:consent",
            old_values=None,
            new_values=consent_data,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data={
                "application_id": application_id,
                "consent_fingerprint": consent_fingerprint,
                "consent_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def log_application_submitted(
        self,
        user_id: str,
        application_id: str,
        submission_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log final application submission."""
        await self.log_onboarding_action(
            user_id=user_id,
            action="onboarding_application_submitted",
            resource_type="onboarding_application",
            resource_id=application_id,
            old_values=None,
            new_values=submission_data,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data={"milestone": "application_submitted"}
        )
    
    async def log_status_change(
        self,
        user_id: str,
        application_id: str,
        from_status: str,
        to_status: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log application status change."""
        await self.log_onboarding_action(
            user_id=user_id,
            action="application_status_changed",
            resource_type="loan_application",
            resource_id=application_id,
            old_values={"status": from_status},
            new_values={"status": to_status, "reason": reason},
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data={
                "from_status": from_status,
                "to_status": to_status,
                "status_change_reason": reason
            }
        )
    
    async def log_validation_error(
        self,
        user_id: str,
        application_id: str,
        step_number: int,
        validation_errors: List[str],
        ip_address: Optional[str] = None
    ):
        """Log validation errors during onboarding."""
        await self.log_onboarding_action(
            user_id=user_id,
            action="validation_error",
            resource_type="onboarding_application",
            resource_id=application_id,
            old_values=None,
            new_values={"errors": validation_errors},
            ip_address=ip_address,
            additional_data={
                "step_number": step_number,
                "error_count": len(validation_errors)
            }
        )
    
    def _create_consent_fingerprint(
        self,
        consent_data: Dict[str, Any],
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> str:
        """Create a unique fingerprint for consent verification."""
        import hashlib
        
        # Create a string representation of the consent
        consent_string = json.dumps(consent_data, sort_keys=True)
        timestamp = datetime.utcnow().isoformat()
        
        # Include context for uniqueness
        fingerprint_data = f"{consent_string}|{timestamp}|{ip_address}|{user_agent}"
        
        # Generate SHA-256 hash
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    async def get_application_audit_trail(
        self,
        application_id: str,
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get complete audit trail for an onboarding application."""
        try:
            from sqlalchemy import select
            
            # Query audit logs for this application
            stmt = select(AuditLog).where(
                AuditLog.resource_id == application_id
            ).order_by(AuditLog.timestamp.desc())
            
            result = await session.execute(stmt)
            audit_logs = result.scalars().all()
            
            # Convert to dictionaries for JSON serialization
            audit_trail = []
            for log in audit_logs:
                audit_trail.append({
                    'id': str(log.id),
                    'action': log.action,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'timestamp': log.timestamp.isoformat(),
                    'user_id': str(log.user_id) if log.user_id else None,
                    'ip_address': log.ip_address,
                    'additional_data': log.additional_data
                })
            
            return audit_trail
            
        except Exception as e:
            logger.error(f"Failed to get audit trail for application {application_id}: {str(e)}")
            return []