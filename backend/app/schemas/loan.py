from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import uuid

from app.models.loan import LoanType, ApplicationStatus, CreditBand, DecisionType


class LoanApplicationCreate(BaseModel):
    loan_type: LoanType
    requested_amount: Decimal = Field(..., gt=0, description="Requested loan amount")
    loan_purpose: str = Field(..., min_length=10, max_length=500, description="Purpose of the loan")
    repayment_period_months: int = Field(..., ge=6, le=60, description="Repayment period in months")
    additional_notes: Optional[str] = Field(None, max_length=1000)

    @validator('requested_amount')
    def validate_requested_amount(cls, v):
        if v <= 0:
            raise ValueError('Requested amount must be greater than 0')
        if v > Decimal('1000000'):  # $1M limit
            raise ValueError('Requested amount cannot exceed $1,000,000')
        return v

    @validator('loan_purpose')
    def validate_loan_purpose(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Loan purpose must be at least 10 characters')
        return v.strip()


class LoanApplicationUpdate(BaseModel):
    loan_type: Optional[LoanType] = None
    requested_amount: Optional[Decimal] = Field(None, gt=0)
    loan_purpose: Optional[str] = Field(None, min_length=10, max_length=500)
    repayment_period_months: Optional[int] = Field(None, ge=6, le=60)
    additional_notes: Optional[str] = Field(None, max_length=1000)

    @validator('requested_amount')
    def validate_requested_amount(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Requested amount must be greater than 0')
            if v > Decimal('1000000'):
                raise ValueError('Requested amount cannot exceed $1,000,000')
        return v


class CreditScoreResponse(BaseModel):
    id: uuid.UUID
    score: int
    credit_band: CreditBand
    score_version: str
    scorecard_name: Optional[str]
    score_breakdown: dict
    contributing_factors: Optional[dict]
    risk_factors: Optional[dict]
    is_valid: bool
    is_overridden: bool
    override_reason: Optional[str]
    bureau_score: Optional[int]
    scored_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class LoanDecisionResponse(BaseModel):
    id: uuid.UUID
    decision: str
    decision_type: DecisionType
    confidence_score: Optional[Decimal]
    decision_reason: Optional[str]
    decision_factors: Optional[dict]
    recommended_amount: Optional[Decimal]
    recommended_term_months: Optional[int]
    recommended_interest_rate: Optional[Decimal]
    conditions: Optional[dict]
    review_level: int
    requires_escalation: bool
    is_override: bool
    decision_date: datetime

    class Config:
        from_attributes = True


class LoanApplicationResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    application_number: str
    loan_type: LoanType
    requested_amount: Decimal
    approved_amount: Optional[Decimal]
    loan_purpose: str
    repayment_period_months: int
    status: ApplicationStatus
    priority: Optional[str]
    assigned_officer_id: Optional[uuid.UUID]
    branch_code: Optional[str]
    review_notes: Optional[str]
    decision_date: Optional[datetime]
    rejection_reason: Optional[str]
    cancellation_reason: Optional[str]
    risk_level: Optional[str]
    requires_collateral: bool
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Nested objects
    latest_credit_score: Optional[CreditScoreResponse]
    latest_decision: Optional[LoanDecisionResponse]
    
    # Computed properties
    is_approved: bool
    is_rejected: bool
    is_cancelled: bool
    is_active: bool
    is_completed: bool
    can_be_cancelled_by_customer: bool

    class Config:
        from_attributes = True


class LoanApplicationListResponse(BaseModel):
    applications: List[LoanApplicationResponse]
    total: int
    page: int
    size: int
    pages: int


class LoanApplicationSubmitRequest(BaseModel):
    confirm_submission: bool = Field(..., description="Confirmation that user wants to submit")
    
    @validator('confirm_submission')
    def validate_confirmation(cls, v):
        if not v:
            raise ValueError('You must confirm submission')
        return v


class LoanApplicationSubmitResponse(BaseModel):
    message: str
    application: LoanApplicationResponse
    next_steps: List[str]


class LoanDecisionCreate(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected|pending)$")
    decision_reason: Optional[str] = None
    recommended_amount: Optional[Decimal] = Field(None, gt=0)
    recommended_term_months: Optional[int] = Field(None, ge=6, le=60)
    recommended_interest_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    conditions: Optional[dict] = None
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None

    @validator('decision_reason')
    def validate_rejection_reason(cls, v, values):
        if values.get('decision') == 'rejected' and not v:
            raise ValueError('Rejection reason is required when rejecting an application')
        return v

    @validator('escalation_reason')
    def validate_escalation_reason(cls, v, values):
        if values.get('requires_escalation') and not v:
            raise ValueError('Escalation reason is required when escalation is needed')
        return v


class ApplicationStatusResponse(BaseModel):
    status: ApplicationStatus
    status_display: dict
    can_be_cancelled: bool
    can_be_submitted: bool
    next_possible_statuses: List[str]
    status_history: List[dict]


class LoanEligibilityCheckResponse(BaseModel):
    is_eligible: bool
    eligibility_reasons: List[str]
    max_loan_amount: Optional[Decimal]
    recommended_loan_types: List[LoanType]
    requirements: List[str]


# Request/Response for bulk operations
class BulkLoanApplicationsRequest(BaseModel):
    application_ids: List[uuid.UUID]
    action: str = Field(..., pattern="^(assign|unassign|bulk_approve|bulk_reject)$")
    officer_id: Optional[uuid.UUID] = None
    reason: Optional[str] = None


class BulkLoanApplicationsResponse(BaseModel):
    success_count: int
    failed_count: int
    errors: List[str]
    updated_applications: List[LoanApplicationResponse]