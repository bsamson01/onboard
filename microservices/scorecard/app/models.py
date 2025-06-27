"""
Pydantic models for scorecard microservice
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


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
    city: str = Field(..., description="Customer's city")
    state: str = Field(..., description="Customer's state/province")
    country: str = Field(..., description="Customer's country")


class CustomerProfile(BaseModel):
    age: int = Field(..., ge=18, le=100, description="Customer's age")
    gender: Gender = Field(..., description="Customer's gender")
    marital_status: MaritalStatus = Field(..., description="Customer's marital status")
    nationality: str = Field(..., description="Customer's nationality")
    location: Location = Field(..., description="Customer's location information")


class FinancialProfile(BaseModel):
    employment_status: EmploymentStatus = Field(..., description="Current employment status")
    monthly_income: float = Field(..., gt=0, description="Monthly income in USD")
    employment_duration_months: int = Field(..., ge=0, description="Duration of current employment in months")
    has_bank_account: bool = Field(..., description="Whether customer has a bank account")
    bank_account_type: BankAccountType = Field(..., description="Type of bank account")
    has_other_loans: bool = Field(..., description="Whether customer has other existing loans")
    other_loans_count: int = Field(..., ge=0, description="Number of other loans")
    total_other_loans_amount: float = Field(..., ge=0, description="Total amount of other loans")

    @validator('total_other_loans_amount')
    def validate_other_loans_amount(cls, v, values):
        if values.get('has_other_loans') and v <= 0:
            raise ValueError("Total other loans amount must be greater than 0 if has_other_loans is True")
        return v


class RiskFactors(BaseModel):
    income_stability: IncomeStability = Field(..., description="Assessment of income stability")
    debt_to_income_ratio: float = Field(..., ge=0, le=10, description="Debt to income ratio")
    employment_stability: EmploymentStability = Field(..., description="Assessment of employment stability")


class RequestMetadata(BaseModel):
    timestamp: datetime = Field(..., description="Request timestamp")
    scorecard_version: str = Field(..., description="Scorecard algorithm version")
    request_id: str = Field(..., description="Unique request identifier")


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