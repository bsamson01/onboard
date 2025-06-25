"""
MFI Configuration models for managing external services and institution-specific settings.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, JSONB, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.database import Base

class ServiceType(str, Enum):
    """Types of external services."""
    SCORECARD = "scorecard"
    CREDIT_BUREAU = "credit_bureau"
    SMS_GATEWAY = "sms_gateway"
    EMAIL_SERVICE = "email_service"
    PAYMENT_GATEWAY = "payment_gateway"
    DOCUMENT_VERIFICATION = "document_verification"
    KYC_SERVICE = "kyc_service"

class ServiceStatus(str, Enum):
    """Service configuration status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    ERROR = "error"

class MFIInstitution(Base):
    """MFI Institution configuration."""
    __tablename__ = "mfi_institutions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Institution Information
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)  # Unique institution code
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Contact Information
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    website_url = Column(String(500))
    
    # Address Information
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state_province = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Operational Settings
    is_active = Column(Boolean, default=True)
    timezone = Column(String(50), default="UTC")
    currency = Column(String(10), default="USD")
    language = Column(String(10), default="en")
    
    # Business Configuration
    business_model = Column(String(50))  # group_lending, individual_lending, both
    max_loan_amount = Column(Integer)
    min_loan_amount = Column(Integer)
    default_loan_term_months = Column(Integer, default=12)
    
    # Scoring Configuration
    minimum_credit_score = Column(Integer, default=600)
    score_validity_days = Column(Integer, default=30)
    require_guarantor_threshold = Column(Integer, default=500)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    service_configs = relationship("ExternalServiceConfig", back_populates="institution", cascade="all, delete-orphan")
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<MFIInstitution(id={self.id}, code={self.code}, name={self.name})>"

class ExternalServiceConfig(Base):
    """Configuration for external services per MFI."""
    __tablename__ = "external_service_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("mfi_institutions.id", ondelete="CASCADE"), nullable=False)
    
    # Service Information
    service_type = Column(String(50), nullable=False)  # ServiceType enum values
    service_name = Column(String(255), nullable=False)
    service_provider = Column(String(255))  # Name of the service provider
    service_version = Column(String(50), default="v1.0")
    
    # Configuration
    api_url = Column(String(500), nullable=False)
    api_key = Column(Text)  # Encrypted API key
    api_secret = Column(Text)  # Encrypted API secret
    username = Column(String(255))  # For basic auth services
    password = Column(Text)  # Encrypted password
    
    # Connection Settings
    timeout_seconds = Column(Integer, default=30)
    retry_attempts = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=5)
    
    # Configuration Parameters
    config_parameters = Column(JSONB)  # Service-specific configuration
    headers = Column(JSONB)  # Custom headers
    
    # Status and Health
    status = Column(String(20), default=ServiceStatus.INACTIVE)
    is_primary = Column(Boolean, default=False)  # Primary service for this type
    priority = Column(Integer, default=1)  # Priority when multiple services available
    
    # Health Monitoring
    last_health_check = Column(DateTime(timezone=True))
    last_successful_call = Column(DateTime(timezone=True))
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    
    # Business Rules
    business_rules = Column(JSONB)  # Service-specific business rules
    rate_limits = Column(JSONB)  # Rate limiting configuration
    
    # Metadata
    description = Column(Text)
    documentation_url = Column(String(500))
    support_contact = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    last_modified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    institution = relationship("MFIInstitution", back_populates="service_configs")
    created_by = relationship("User", foreign_keys=[created_by_id])
    last_modified_by = relationship("User", foreign_keys=[last_modified_by_id])
    
    def __repr__(self):
        return f"<ExternalServiceConfig(id={self.id}, service_type={self.service_type}, institution={self.institution.code})>"
    
    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy based on recent activity."""
        if not self.last_health_check:
            return False
        
        # Consider healthy if checked within last 5 minutes and no recent errors
        time_threshold = datetime.utcnow() - timedelta(minutes=5)
        return (
            self.last_health_check > time_threshold and
            self.status == ServiceStatus.ACTIVE and
            self.error_count < 5  # Allow some errors
        )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100

class ServiceEndpoint(Base):
    """Specific endpoints for external services."""
    __tablename__ = "service_endpoints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_config_id = Column(UUID(as_uuid=True), ForeignKey("external_service_configs.id", ondelete="CASCADE"), nullable=False)
    
    # Endpoint Information
    endpoint_name = Column(String(255), nullable=False)  # e.g., "calculate_score", "verify_identity"
    endpoint_path = Column(String(500), nullable=False)  # e.g., "/api/v1/score"
    http_method = Column(String(10), default="POST")  # GET, POST, PUT, DELETE
    
    # Configuration
    request_template = Column(JSONB)  # Template for request payload
    response_mapping = Column(JSONB)  # How to map response fields
    validation_rules = Column(JSONB)  # Input validation rules
    
    # Settings
    cache_ttl_seconds = Column(Integer, default=0)  # Cache time-to-live
    is_async = Column(Boolean, default=False)  # Whether endpoint supports async calls
    requires_auth = Column(Boolean, default=True)
    
    # Monitoring
    avg_response_time_ms = Column(Integer, default=0)
    last_call_time = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    service_config = relationship("ExternalServiceConfig")
    
    def __repr__(self):
        return f"<ServiceEndpoint(id={self.id}, name={self.endpoint_name}, method={self.http_method})>"

class ServiceCallLog(Base):
    """Log of external service calls for monitoring and debugging."""
    __tablename__ = "service_call_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_config_id = Column(UUID(as_uuid=True), ForeignKey("external_service_configs.id", ondelete="CASCADE"), nullable=False)
    endpoint_id = Column(UUID(as_uuid=True), ForeignKey("service_endpoints.id"))
    
    # Call Information
    request_id = Column(String(255))  # Unique request identifier
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(String(255))
    
    # Request Details
    request_method = Column(String(10))
    request_url = Column(String(1000))
    request_headers = Column(JSONB)
    request_payload = Column(JSONB)
    
    # Response Details
    response_status_code = Column(Integer)
    response_headers = Column(JSONB)
    response_payload = Column(JSONB)
    response_time_ms = Column(Integer)
    
    # Status
    success = Column(Boolean)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Business Context
    business_context = Column(JSONB)  # What triggered this call
    application_id = Column(String(255))  # Related application if applicable
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    service_config = relationship("ExternalServiceConfig")
    endpoint = relationship("ServiceEndpoint")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ServiceCallLog(id={self.id}, success={self.success}, response_time={self.response_time_ms}ms)>"

# Index definitions for performance
from sqlalchemy import Index

# Indexes for efficient querying
Index('idx_mfi_institutions_code', MFIInstitution.code)
Index('idx_mfi_institutions_active', MFIInstitution.is_active)
Index('idx_service_configs_institution_type', ExternalServiceConfig.institution_id, ExternalServiceConfig.service_type)
Index('idx_service_configs_status', ExternalServiceConfig.status)
Index('idx_service_configs_primary', ExternalServiceConfig.is_primary)
Index('idx_service_call_logs_service_time', ServiceCallLog.service_config_id, ServiceCallLog.started_at)
Index('idx_service_call_logs_success', ServiceCallLog.success)
Index('idx_service_call_logs_application', ServiceCallLog.application_id)