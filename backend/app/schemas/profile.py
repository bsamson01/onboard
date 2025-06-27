from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.user import UserRole, UserState
from app.models.onboarding import DocumentType, DocumentStatus


class ProfileStatusResponse(BaseModel):
    """User profile status response."""
    user_state: UserState
    completion_percentage: float
    needs_profile_update: bool
    is_profile_outdated: bool
    onboarding_completed_at: Optional[datetime]
    last_profile_update: Optional[datetime]
    profile_expiry_date: Optional[datetime]
    can_create_loans: bool


class UserProfileResponse(BaseModel):
    """Complete user profile response."""
    # Basic User Info
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    role: UserRole
    user_state: UserState
    
    # Profile Status
    is_active: bool
    is_verified: bool
    is_locked: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    # Profile Management
    onboarding_completed_at: Optional[datetime]
    last_profile_update: Optional[datetime]
    profile_expiry_date: Optional[datetime]
    profile_completion_percentage: float
    can_create_loans: bool
    
    # Customer Data (if available)
    customer_data: Optional[Dict[str, Any]] = None
    documents_count: int = 0
    verified_documents_count: int = 0


class ProfileUpdateRequest(BaseModel):
    """Request to update user profile information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    
    # Personal Information
    date_of_birth: Optional[str] = None  # YYYY-MM-DD format
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    id_number: Optional[str] = None
    id_type: Optional[str] = None
    
    # Contact Information
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    
    # Employment Information
    employment_status: Optional[str] = None
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    monthly_income: Optional[float] = None
    employment_duration_months: Optional[int] = None
    
    # Financial Information
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_type: Optional[str] = None
    has_other_loans: Optional[bool] = None
    other_loans_details: Optional[Dict[str, Any]] = None
    
    # Consent and Preferences
    consent_data_processing: Optional[bool] = None
    consent_credit_check: Optional[bool] = None
    consent_marketing: Optional[bool] = None
    preferred_communication: Optional[str] = None


class DocumentResponse(BaseModel):
    """Document information response."""
    id: str
    document_type: DocumentType
    document_name: str
    status: DocumentStatus
    is_required: bool
    expires_at: Optional[str] = None  # YYYY-MM-DD format
    is_expired: bool
    uploaded_at: datetime
    verified_at: Optional[datetime]
    verification_notes: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]


class DocumentUploadResponse(BaseModel):
    """Document upload response."""
    document_id: str
    document_type: DocumentType
    document_name: str
    status: DocumentStatus
    file_size: int
    mime_type: str
    uploaded_at: datetime


class DocumentVerificationRequest(BaseModel):
    """Request to verify a document (admin only)."""
    status: DocumentStatus
    verification_notes: Optional[str] = None
    
    @validator('status')
    def validate_verification_status(cls, v):
        if v not in [DocumentStatus.VERIFIED, DocumentStatus.REJECTED]:
            raise ValueError('Status must be VERIFIED or REJECTED for verification')
        return v


class RoleUpdateRequest(BaseModel):
    """Request to update user role (admin only)."""
    new_role: UserRole
    reason: Optional[str] = None


class StateUpdateRequest(BaseModel):
    """Request to update user state (admin only)."""
    new_state: UserState
    reason: Optional[str] = None


class UserRoleHistoryResponse(BaseModel):
    """User role change history response."""
    id: str
    user_id: str
    old_role: Optional[str]
    new_role: str
    changed_by_id: Optional[str]
    changed_by_name: Optional[str]
    changed_at: datetime
    reason: Optional[str]


class AdminUserProfileResponse(BaseModel):
    """Extended user profile response for admin view."""
    # All fields from UserProfileResponse
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    role: UserRole
    user_state: UserState
    is_active: bool
    is_verified: bool
    is_locked: bool
    failed_login_attempts: int
    last_login: Optional[datetime]
    created_at: datetime
    
    # Profile Management
    onboarding_completed_at: Optional[datetime]
    last_profile_update: Optional[datetime]
    profile_expiry_date: Optional[datetime]
    profile_completion_percentage: float
    can_create_loans: bool
    
    # Extended Admin Info
    customer_data: Optional[Dict[str, Any]] = None
    documents: List[DocumentResponse] = []
    role_history: List[UserRoleHistoryResponse] = []
    
    # Statistics
    total_applications: int = 0
    approved_applications: int = 0
    rejected_applications: int = 0
    pending_applications: int = 0


class ProfileUpdateRequiredResponse(BaseModel):
    """Response indicating if profile update is required."""
    update_required: bool
    reason: Optional[str] = None
    expired_fields: List[str] = []
    missing_documents: List[DocumentType] = []
    required_actions: List[str] = []


class BulkUserOperationRequest(BaseModel):
    """Request for bulk operations on multiple users."""
    user_ids: List[str]
    operation: str  # 'activate', 'deactivate', 'verify', 'lock', 'unlock'
    reason: Optional[str] = None


class BulkUserOperationResponse(BaseModel):
    """Response for bulk user operations."""
    success_count: int
    failure_count: int
    total_count: int
    failed_user_ids: List[str] = []
    errors: List[str] = []