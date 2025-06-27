from pydantic import BaseModel, EmailStr, validator, Field, constr, conint
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import re

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
    # Basic User Information with validation
    first_name: Optional[constr(min_length=1, max_length=100, strip_whitespace=True)] = Field(None, description="First name (1-100 characters)")
    last_name: Optional[constr(min_length=1, max_length=100, strip_whitespace=True)] = Field(None, description="Last name (1-100 characters)")
    phone_number: Optional[constr(min_length=10, max_length=20)] = Field(None, description="Phone number (10-20 characters)")
    
    # Personal Information with validation
    date_of_birth: Optional[str] = Field(None, description="Date of birth in YYYY-MM-DD format")
    gender: Optional[constr(max_length=10)] = Field(None, description="Gender")
    marital_status: Optional[constr(max_length=20)] = Field(None, description="Marital status")
    nationality: Optional[constr(max_length=50)] = Field(None, description="Nationality")
    id_number: Optional[constr(min_length=5, max_length=50)] = Field(None, description="ID number (5-50 characters)")
    id_type: Optional[constr(max_length=20)] = Field(None, description="ID type")
    
    # Contact Information with validation
    address_line1: Optional[constr(max_length=255, strip_whitespace=True)] = Field(None, description="Address line 1")
    address_line2: Optional[constr(max_length=255, strip_whitespace=True)] = Field(None, description="Address line 2")
    city: Optional[constr(max_length=100, strip_whitespace=True)] = Field(None, description="City")
    state_province: Optional[constr(max_length=100, strip_whitespace=True)] = Field(None, description="State/Province")
    postal_code: Optional[constr(max_length=20, strip_whitespace=True)] = Field(None, description="Postal code")
    country: Optional[constr(max_length=50, strip_whitespace=True)] = Field(None, description="Country")
    
    # Emergency Contact with validation
    emergency_contact_name: Optional[constr(max_length=200, strip_whitespace=True)] = Field(None, description="Emergency contact name")
    emergency_contact_phone: Optional[constr(min_length=10, max_length=20)] = Field(None, description="Emergency contact phone")
    emergency_contact_relationship: Optional[constr(max_length=50)] = Field(None, description="Emergency contact relationship")
    
    # Employment Information with validation
    employment_status: Optional[constr(max_length=50)] = Field(None, description="Employment status")
    employer_name: Optional[constr(max_length=255, strip_whitespace=True)] = Field(None, description="Employer name")
    job_title: Optional[constr(max_length=100, strip_whitespace=True)] = Field(None, description="Job title")
    monthly_income: Optional[float] = Field(None, ge=0, le=10000000, description="Monthly income (0-10M)")
    employment_duration_months: Optional[conint(ge=0, le=600)] = Field(None, description="Employment duration in months (0-600)")
    
    # Financial Information with validation
    bank_name: Optional[constr(max_length=100, strip_whitespace=True)] = Field(None, description="Bank name")
    bank_account_number: Optional[constr(min_length=5, max_length=50)] = Field(None, description="Bank account number")
    bank_account_type: Optional[constr(max_length=20)] = Field(None, description="Bank account type")
    has_other_loans: Optional[bool] = Field(None, description="Has other loans")
    other_loans_details: Optional[Dict[str, Any]] = Field(None, description="Other loans details")
    
    # Consent and Preferences
    consent_data_processing: Optional[bool] = Field(None, description="Consent for data processing")
    consent_credit_check: Optional[bool] = Field(None, description="Consent for credit check")
    consent_marketing: Optional[bool] = Field(None, description="Consent for marketing")
    preferred_communication: Optional[constr(max_length=20)] = Field(None, description="Preferred communication method")
    
    @validator('phone_number', 'emergency_contact_phone')
    def validate_phone_number(cls, v):
        if v is not None:
            # Remove all non-digit characters
            digits_only = re.sub(r'\D', '', v)
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValueError('Phone number must contain 10-15 digits')
            # Check for valid international format
            if not re.match(r'^[\+]?[1-9][\d\-\(\)\s]*\d$', v):
                raise ValueError('Invalid phone number format')
        return v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if v is not None:
            try:
                birth_date = date.fromisoformat(v)
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                if age < 18 or age > 120:
                    raise ValueError('Age must be between 18 and 120 years')
                if birth_date > today:
                    raise ValueError('Date of birth cannot be in the future')
            except ValueError as e:
                if 'Invalid isoformat string' in str(e):
                    raise ValueError('Date must be in YYYY-MM-DD format')
                raise e
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        if v is not None:
            valid_genders = ['male', 'female', 'other', 'prefer_not_to_say']
            if v.lower() not in valid_genders:
                raise ValueError(f'Gender must be one of: {", ".join(valid_genders)}')
        return v
    
    @validator('marital_status')
    def validate_marital_status(cls, v):
        if v is not None:
            valid_statuses = ['single', 'married', 'divorced', 'widowed', 'separated', 'domestic_partnership']
            if v.lower() not in valid_statuses:
                raise ValueError(f'Marital status must be one of: {", ".join(valid_statuses)}')
        return v
    
    @validator('employment_status')
    def validate_employment_status(cls, v):
        if v is not None:
            valid_statuses = ['employed', 'self_employed', 'unemployed', 'student', 'retired', 'other']
            if v.lower() not in valid_statuses:
                raise ValueError(f'Employment status must be one of: {", ".join(valid_statuses)}')
        return v
    
    @validator('bank_account_type')
    def validate_bank_account_type(cls, v):
        if v is not None:
            valid_types = ['checking', 'savings', 'current', 'fixed_deposit', 'other']
            if v.lower() not in valid_types:
                raise ValueError(f'Bank account type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('preferred_communication')
    def validate_preferred_communication(cls, v):
        if v is not None:
            valid_methods = ['email', 'sms', 'phone', 'postal']
            if v.lower() not in valid_methods:
                raise ValueError(f'Preferred communication must be one of: {", ".join(valid_methods)}')
        return v
    
    @validator('id_number')
    def validate_id_number(cls, v):
        if v is not None:
            # Remove spaces and special characters for validation
            clean_id = re.sub(r'[\s\-]', '', v)
            if not re.match(r'^[A-Z0-9]+$', clean_id.upper()):
                raise ValueError('ID number can only contain letters and numbers')
        return v
    
    @validator('bank_account_number')
    def validate_bank_account_number(cls, v):
        if v is not None:
            # Remove spaces and special characters for validation
            clean_account = re.sub(r'[\s\-]', '', v)
            if not re.match(r'^[A-Z0-9]+$', clean_account.upper()):
                raise ValueError('Bank account number can only contain letters and numbers')
        return v
    
    @validator('other_loans_details')
    def validate_other_loans_details(cls, v):
        if v is not None:
            # Ensure it's a dictionary with reasonable size
            if not isinstance(v, dict):
                raise ValueError('Other loans details must be a dictionary')
            if len(str(v)) > 5000:  # Limit JSON size
                raise ValueError('Other loans details too large (max 5000 characters)')
        return v


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
    new_role: UserRole = Field(..., description="New role to assign")
    reason: Optional[constr(max_length=500, strip_whitespace=True)] = Field(None, description="Reason for role change (max 500 characters)")
    
    @validator('reason')
    def validate_reason(cls, v):
        if v is not None and len(v.strip()) < 3:
            raise ValueError('Reason must be at least 3 characters long')
        return v


class StateUpdateRequest(BaseModel):
    """Request to update user state (admin only)."""
    new_state: UserState = Field(..., description="New state to assign")
    reason: Optional[constr(max_length=500, strip_whitespace=True)] = Field(None, description="Reason for state change (max 500 characters)")
    
    @validator('reason')
    def validate_reason(cls, v):
        if v is not None and len(v.strip()) < 3:
            raise ValueError('Reason must be at least 3 characters long')
        return v


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
    user_ids: List[constr(min_length=1)] = Field(..., min_items=1, max_items=100, description="List of user IDs (1-100 users)")
    operation: constr(regex=r'^(activate|deactivate|verify|lock|unlock)$') = Field(..., description="Operation to perform")
    reason: Optional[constr(max_length=500, strip_whitespace=True)] = Field(None, description="Reason for bulk operation")
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if not v:
            raise ValueError('At least one user ID is required')
        if len(v) > 100:
            raise ValueError('Cannot process more than 100 users at once')
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError('Duplicate user IDs are not allowed')
        # Validate UUID format
        import uuid
        for user_id in v:
            try:
                uuid.UUID(user_id)
            except ValueError:
                raise ValueError(f'Invalid user ID format: {user_id}')
        return v
    
    @validator('reason')
    def validate_reason(cls, v):
        if v is not None and len(v.strip()) < 3:
            raise ValueError('Reason must be at least 3 characters long')
        return v


class BulkUserOperationResponse(BaseModel):
    """Response for bulk user operations."""
    success_count: int
    failure_count: int
    total_count: int
    failed_user_ids: List[str] = []
    errors: List[str] = []