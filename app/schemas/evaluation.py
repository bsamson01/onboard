from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class EvaluationRequest(BaseModel):
    """Schema for scorecard evaluation requests."""
    scorecard_uuid: str = Field(..., description="UUID of scorecard to use")
    applicant_id: str = Field(..., description="Unique applicant identifier")
    applicant_data: Dict[str, Any] = Field(..., description="Applicant data for scoring")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    user_id: Optional[str] = Field(None, description="User making the request")
    source_system: Optional[str] = Field(None, description="Source system identifier")
    use_version: Optional[int] = Field(None, description="Specific version to use")
    
    @validator('applicant_data')
    def validate_applicant_data(cls, v):
        """Ensure applicant data is not empty."""
        if not v:
            raise ValueError('Applicant data cannot be empty')
        return v


class FactorScore(BaseModel):
    """Individual factor score breakdown."""
    factor_code: str
    factor_name: str
    points: int
    max_points: int
    value: Any
    reasoning: str
    weight: float


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown."""
    total_score: int
    max_possible_score: int
    letter_grade: str
    eligibility: bool
    factor_scores: List[FactorScore]
    summary: str
    warnings: List[str] = []


class ScoreResultResponse(BaseModel):
    """Schema for score result responses."""
    id: int
    uuid: str
    scorecard_id: int
    version_id: int
    applicant_id: str
    total_score: int
    letter_grade: str
    eligibility: bool
    factor_scores: List[Dict[str, Any]]
    breakdown: ScoreBreakdown
    processing_time_ms: Optional[int]
    data_completeness: Optional[float]
    confidence_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationLogResponse(BaseModel):
    """Schema for evaluation log responses."""
    id: int
    uuid: str
    score_result_id: int
    request_id: Optional[str]
    user_id: Optional[str]
    source_system: Optional[str]
    input_data_hash: Optional[str]
    data_sources: Optional[List[str]]
    evaluation_steps: Optional[List[Dict[str, Any]]]
    warnings: Optional[List[str]]
    errors: Optional[List[str]]
    processing_time_ms: Optional[int]
    memory_usage_mb: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True