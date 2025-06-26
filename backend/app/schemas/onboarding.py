from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, validator, Field
from enum import Enum
import uuid

from app.models.onboarding import OnboardingStatus, DocumentType, DocumentStatus


class OnboardingStepRequest(BaseModel):
    step_number: int = Field(..., ge=1, le=5)
    step_data: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "step_data": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "date_of_birth": "1990-01-15",
                    "gender": "male",
                    "marital_status": "single",
                    "nationality": "US",
                    "id_number": "123456789",
                    "id_type": "national_id"
                }
            }
        }


class PersonalInfoRequest(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date
    gender: str = Field(..., pattern="^(male|female|other)$")
    marital_status: str = Field(..., pattern="^(single|married|divorced|widowed)$")
    nationality: str = Field(..., min_length=2, max_length=50)
    id_number: str = Field(..., min_length=5, max_length=50)
    id_type: str = Field(default="national_id", pattern="^(national_id|passport|drivers_license)$")

    @validator('date_of_birth')
    def validate_age(cls, v):
        from datetime import date
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('Must be at least 18 years old')
        if age > 100:
            raise ValueError('Invalid birth date')
        return v


class ContactInfoRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: EmailStr
    address_line1: str = Field(..., min_length=5, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state_province: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(..., min_length=2, max_length=50)
    emergency_contact_name: str = Field(..., min_length=2, max_length=200)
    emergency_contact_phone: str = Field(..., min_length=10, max_length=20)
    emergency_contact_relationship: str = Field(..., min_length=2, max_length=50)


class FinancialProfileRequest(BaseModel):
    employment_status: str = Field(..., pattern="^(employed|self_employed|unemployed|student|retired)$")
    employer_name: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=100)
    monthly_income: float = Field(..., ge=0)
    employment_duration_months: Optional[int] = Field(None, ge=0)
    bank_name: str = Field(..., min_length=2, max_length=100)
    bank_account_number: str = Field(..., min_length=5, max_length=50)
    bank_account_type: str = Field(..., pattern="^(savings|checking|current)$")
    has_other_loans: bool = Field(default=False)
    other_loans_details: Optional[List[Dict[str, Any]]] = Field(default=None)

    @validator('employer_name')
    def validate_employer_name(cls, v, values):
        if values.get('employment_status') in ['employed', 'self_employed'] and not v:
            raise ValueError('Employer name is required for employed individuals')
        return v

    @validator('job_title')
    def validate_job_title(cls, v, values):
        if values.get('employment_status') == 'employed' and not v:
            raise ValueError('Job title is required for employed individuals')
        return v


class ConsentRequest(BaseModel):
    consent_data_processing: bool = Field(...)
    consent_credit_check: bool = Field(...)
    consent_marketing: bool = Field(default=False)
    preferred_communication: str = Field(default="email", pattern="^(email|sms|phone)$")

    @validator('consent_data_processing')
    def validate_data_processing_consent(cls, v):
        if not v:
            raise ValueError('Data processing consent is required')
        return v

    @validator('consent_credit_check')
    def validate_credit_check_consent(cls, v):
        if not v:
            raise ValueError('Credit check consent is required')
        return v


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    document_type: DocumentType
    document_name: str
    file_path: str
    file_size: int
    status: DocumentStatus
    uploaded_at: datetime
    ocr_confidence: Optional[float] = None
    extracted_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class OnboardingStepResponse(BaseModel):
    id: uuid.UUID
    step_number: int
    step_name: str
    is_completed: bool
    completed_at: Optional[datetime] = None
    step_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class EligibilityResult(BaseModel):
    score: int = Field(..., ge=0, le=1000)
    grade: str = Field(..., pattern="^(AA|A|B|C|D)$")
    eligibility: str = Field(..., pattern="^(eligible|ineligible|pending)$")
    message: str
    breakdown: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None


class OnboardingApplicationResponse(BaseModel):
    id: uuid.UUID
    application_number: str
    status: OnboardingStatus
    current_step: int
    total_steps: int
    progress_percentage: float
    steps: List[OnboardingStepResponse]
    eligibility_result: Optional[EligibilityResult] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OnboardingApplicationCreate(BaseModel):
    pass  # No initial data required for creation


class OnboardingApplicationUpdate(BaseModel):
    status: Optional[OnboardingStatus] = None
    current_step: Optional[int] = None
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class CustomerProfileResponse(BaseModel):
    id: uuid.UUID
    customer_number: Optional[str] = None
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OnboardingProgressResponse(BaseModel):
    application_id: uuid.UUID
    current_step: int
    total_steps: int
    progress_percentage: float
    steps_completed: List[str]
    next_step: Optional[str] = None
    can_proceed: bool
    validation_errors: Optional[List[str]] = None


class OnboardingValidationError(BaseModel):
    field: str
    message: str
    step_number: int


class OnboardingSubmissionResponse(BaseModel):
    application_id: uuid.UUID
    status: OnboardingStatus
    eligibility_result: Optional[EligibilityResult] = None
    next_actions: List[str]
    estimated_processing_time: str
    reference_number: str