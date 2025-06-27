"""
Pydantic models for scorecard microservice
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
import re


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


class EmploymentStatus(str, Enum):
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"
    RETIRED = "retired"


class BankAccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    BOTH = "both"
    NONE = "none"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IncomeStability(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EmploymentStability(str, Enum):
    STABLE = "stable"
    MODERATE = "moderate"
    UNSTABLE = "unstable"


class CreditGrade(str, Enum):
    AA = "AA"
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class EligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    PENDING = "pending"


class Location(BaseModel):
    city: str = Field(..., min_length=1, max_length=100, description="Customer's city")
    state: str = Field(..., min_length=1, max_length=100, description="Customer's state/province")
    country: str = Field(..., min_length=2, max_length=3, description="Customer's country (ISO code)")

    @field_validator('city', 'state')
    @classmethod
    def validate_location_fields(cls, v):
        """Validate location fields are properly formatted"""
        if not v or v.strip() == "":
            raise ValueError("Location fields cannot be empty")
        # Remove extra whitespace and validate length
        cleaned = v.strip()
        if len(cleaned) < 1:
            raise ValueError("Location field too short")
        if len(cleaned) > 100:
            raise ValueError("Location field too long")
        return cleaned.title()

    @field_validator('country')
    @classmethod
    def validate_country_code(cls, v):
        """Validate country is a proper country code"""
        if not re.match(r'^[A-Z]{2,3}$', v.upper()):
            raise ValueError('Country must be a valid 2-3 letter country code')
        return v.upper()


class CustomerProfile(BaseModel):
    age: int = Field(..., ge=18, le=120, description="Customer's age")
    gender: Gender = Field(..., description="Customer's gender")
    marital_status: MaritalStatus = Field(..., description="Customer's marital status")
    nationality: str = Field(..., min_length=2, max_length=3, description="Customer's nationality (ISO country code)")
    location: Location = Field(..., description="Customer's location information")

    @field_validator('nationality')
    @classmethod
    def validate_nationality(cls, v):
        """Validate nationality is a proper country code"""
        if not re.match(r'^[A-Z]{2,3}$', v.upper()):
            raise ValueError('Nationality must be a valid 2-3 letter country code')
        return v.upper()

    @field_validator('age')
    @classmethod
    def validate_age_business_rules(cls, v):
        """Additional business validation for age"""
        if v < 18:
            raise ValueError('Customer must be at least 18 years old')
        if v > 120:
            raise ValueError('Age seems unrealistic')
        return v


class FinancialProfile(BaseModel):
    employment_status: EmploymentStatus = Field(..., description="Current employment status")
    monthly_income: float = Field(..., gt=0, le=1000000, description="Monthly income in USD")
    employment_duration_months: int = Field(..., ge=0, le=600, description="Duration of current employment in months")
    has_bank_account: bool = Field(..., description="Whether customer has a bank account")
    bank_account_type: BankAccountType = Field(..., description="Type of bank account")
    has_other_loans: bool = Field(..., description="Whether customer has other existing loans")
    other_loans_count: int = Field(..., ge=0, le=50, description="Number of other loans")
    total_other_loans_amount: float = Field(..., ge=0, le=10000000, description="Total amount of other loans")

    @field_validator('monthly_income')
    @classmethod
    def validate_income_realistic(cls, v):
        """Validate income is realistic"""
        if v < 100:
            raise ValueError("Monthly income seems too low to be realistic")
        if v > 1000000:
            raise ValueError("Monthly income seems unrealistically high")
        return round(v, 2)

    @field_validator('employment_duration_months')
    @classmethod
    def validate_employment_duration(cls, v):
        """Validate employment duration is reasonable"""
        if v > 600:  # 50 years
            raise ValueError("Employment duration exceeds reasonable limits")
        return v

    @field_validator('other_loans_count')
    @classmethod
    def validate_loan_count_reasonable(cls, v):
        """Validate loan count is reasonable"""
        if v > 50:
            raise ValueError("Number of loans exceeds reasonable limits")
        return v

    @model_validator(mode='after')
    def validate_loan_consistency(self):
        """Cross-field validation for loan-related fields"""
        has_loans = self.has_other_loans
        loan_count = self.other_loans_count
        loan_amount = self.total_other_loans_amount
        
        if has_loans:
            if loan_count == 0:
                raise ValueError("If has_other_loans is True, other_loans_count must be greater than 0")
            if loan_amount <= 0:
                raise ValueError("If has_other_loans is True, total_other_loans_amount must be greater than 0")
        else:
            if loan_count > 0:
                raise ValueError("If has_other_loans is False, other_loans_count must be 0")
            if loan_amount > 0:
                raise ValueError("If has_other_loans is False, total_other_loans_amount must be 0")
                
        return self

    @model_validator(mode='after')
    def validate_bank_account_consistency(self):
        """Validate bank account consistency"""
        has_account = self.has_bank_account
        account_type = self.bank_account_type
        
        if has_account and account_type == BankAccountType.NONE:
            raise ValueError("If has_bank_account is True, bank_account_type cannot be 'none'")
        if not has_account and account_type != BankAccountType.NONE:
            raise ValueError("If has_bank_account is False, bank_account_type must be 'none'")
            
        return self


class RiskFactors(BaseModel):
    income_stability: IncomeStability = Field(..., description="Assessment of income stability")
    debt_to_income_ratio: float = Field(..., ge=0, le=5.0, description="Debt to income ratio")
    employment_stability: EmploymentStability = Field(..., description="Assessment of employment stability")

    @field_validator('debt_to_income_ratio')
    @classmethod
    def validate_debt_ratio(cls, v):
        """Validate debt to income ratio is reasonable"""
        if v < 0:
            raise ValueError("Debt to income ratio cannot be negative")
        if v > 5.0:
            raise ValueError("Debt to income ratio exceeds reasonable limits (5.0)")
        return round(v, 4)


class RequestMetadata(BaseModel):
    timestamp: datetime = Field(..., description="Request timestamp")
    scorecard_version: str = Field(..., min_length=1, max_length=20, description="Scorecard algorithm version")
    request_id: str = Field(..., min_length=5, max_length=100, description="Unique request identifier")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp is reasonable"""
        from datetime import datetime, timedelta, timezone
        
        # Make timestamp timezone-aware if it isn't already
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        
        # Allow some clock skew (5 minutes future, 24 hours past)
        if v > now + timedelta(minutes=5):
            raise ValueError("Timestamp cannot be more than 5 minutes in the future")
        if v < now - timedelta(hours=24):
            raise ValueError("Timestamp cannot be more than 24 hours in the past")
        return v

    @field_validator('scorecard_version')
    @classmethod
    def validate_version_format(cls, v):
        """Validate version format"""
        if not re.match(r'^v?\d+\.\d+(\.\d+)?$', v):
            raise ValueError("Scorecard version must be in format 'v1.0' or '1.0.0'")
        return v

    @field_validator('request_id')
    @classmethod
    def validate_request_id_format(cls, v):
        """Validate request ID format"""
        # Allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Request ID can only contain letters, numbers, hyphens, and underscores")
        return v


class ScoringRequest(BaseModel):
    customer_profile: CustomerProfile = Field(..., description="Customer demographic information")
    financial_profile: FinancialProfile = Field(..., description="Customer financial information")
    risk_factors: RiskFactors = Field(..., description="Risk assessment factors")
    request_metadata: RequestMetadata = Field(..., description="Request metadata")

    class Config:
        schema_extra = {
            "example": {
                "customer_profile": {
                    "age": 35,
                    "gender": "male",
                    "marital_status": "married",
                    "nationality": "US",
                    "location": {
                        "city": "New York",
                        "state": "NY",
                        "country": "US"
                    }
                },
                "financial_profile": {
                    "employment_status": "employed",
                    "monthly_income": 5000.0,
                    "employment_duration_months": 24,
                    "has_bank_account": True,
                    "bank_account_type": "checking",
                    "has_other_loans": False,
                    "other_loans_count": 0,
                    "total_other_loans_amount": 0.0
                },
                "risk_factors": {
                    "income_stability": "high",
                    "debt_to_income_ratio": 0.15,
                    "employment_stability": "stable"
                },
                "request_metadata": {
                    "timestamp": "2024-01-15T10:30:00Z",
                    "scorecard_version": "v1.0",
                    "request_id": "score_20240115_103000"
                }
            }
        }


class ScoreBreakdown(BaseModel):
    base_score: int = Field(..., description="Base credit score before adjustments")
    income_adjustment: int = Field(..., description="Score adjustment based on income")
    final_score: int = Field(..., description="Final calculated score")
    risk_factors: RiskFactors = Field(..., description="Risk factors used in calculation")


class ScoringResponse(BaseModel):
    score: int = Field(..., ge=0, le=1000, description="Credit score on 0-1000 scale")
    grade: CreditGrade = Field(..., description="Credit grade based on score")
    eligibility: EligibilityStatus = Field(..., description="Loan eligibility status")
    message: str = Field(..., description="Human-readable score interpretation")
    breakdown: ScoreBreakdown = Field(..., description="Detailed score calculation breakdown")
    recommendations: List[str] = Field(..., description="Recommendations for credit improvement")

    class Config:
        schema_extra = {
            "example": {
                "score": 720,
                "grade": "A",
                "eligibility": "eligible",
                "message": "Very good credit profile! Your score of 720 qualifies you for competitive rates.",
                "breakdown": {
                    "base_score": 700,
                    "income_adjustment": 20,
                    "final_score": 720,
                    "risk_factors": {
                        "income_stability": "high",
                        "debt_to_income_ratio": 0.15,
                        "employment_stability": "stable"
                    }
                },
                "recommendations": [
                    "Maintain consistent employment history",
                    "Consider providing additional income documentation"
                ]
            }
        }


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Health check timestamp")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "scorecard",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }