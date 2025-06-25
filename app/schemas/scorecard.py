from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class DataType(str, Enum):
    """Supported data types for scoring factors."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"


class ScoringFactorCreate(BaseModel):
    """Schema for creating a new scoring factor."""
    name: str = Field(..., description="Human-readable name of the factor")
    code: str = Field(..., description="Machine-readable code for the factor")
    description: Optional[str] = Field(None, description="Detailed description")
    category: Optional[str] = Field(None, description="Factor category")
    weight: float = Field(1.0, ge=0, le=10, description="Weight in scoring (0-10)")
    data_type: DataType = Field(DataType.NUMERIC, description="Data type")
    rules: Dict[str, Any] = Field(..., description="Scoring rules configuration")
    is_required: bool = Field(True, description="Whether factor is required")
    min_value: Optional[float] = Field(None, description="Minimum allowed value")
    max_value: Optional[float] = Field(None, description="Maximum allowed value")
    default_points: int = Field(0, description="Default points if data missing")

    @validator('code')
    def validate_code(cls, v):
        """Ensure code is valid identifier."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Code must be alphanumeric with underscores only')
        return v.lower()

    @validator('rules')
    def validate_rules(cls, v):
        """Basic validation of scoring rules."""
        if not isinstance(v, dict):
            raise ValueError('Rules must be a dictionary')
        return v


class ScoringFactorResponse(ScoringFactorCreate):
    """Schema for scoring factor responses."""
    id: int
    uuid: str
    version_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ScorecardVersionCreate(BaseModel):
    """Schema for creating a new scorecard version."""
    description: Optional[str] = Field(None, description="Version description")
    scoring_factors: List[ScoringFactorCreate] = Field([], description="Scoring factors")
    config_data: Optional[Dict[str, Any]] = Field(None, description="Additional config")


class ScorecardVersionResponse(BaseModel):
    """Schema for scorecard version responses."""
    id: int
    uuid: str
    scorecard_id: int
    version_number: int
    description: Optional[str]
    is_active: bool
    config_data: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: Optional[str]
    scoring_factors: List[ScoringFactorResponse] = []

    class Config:
        from_attributes = True


class ScorecardConfigCreate(BaseModel):
    """Schema for creating a new scorecard configuration."""
    mfi_id: str = Field(..., description="Microfinance Institution ID")
    name: str = Field(..., description="Scorecard name")
    description: Optional[str] = Field(None, description="Scorecard description")
    min_score: int = Field(300, ge=0, le=1000, description="Minimum possible score")
    max_score: int = Field(850, ge=100, le=1000, description="Maximum possible score")
    passing_score: int = Field(600, ge=0, le=1000, description="Minimum passing score")
    
    @validator('passing_score')
    def validate_passing_score(cls, v, values):
        """Ensure passing score is within min/max range."""
        min_score = values.get('min_score', 300)
        max_score = values.get('max_score', 850)
        if not (min_score <= v <= max_score):
            raise ValueError('Passing score must be between min_score and max_score')
        return v


class ScorecardConfigUpdate(BaseModel):
    """Schema for updating scorecard configuration."""
    name: Optional[str] = None
    description: Optional[str] = None
    min_score: Optional[int] = Field(None, ge=0, le=1000)
    max_score: Optional[int] = Field(None, ge=100, le=1000)
    passing_score: Optional[int] = Field(None, ge=0, le=1000)
    is_active: Optional[bool] = None


class ScorecardConfigResponse(BaseModel):
    """Schema for scorecard configuration responses."""
    id: int
    uuid: str
    mfi_id: str
    name: str
    description: Optional[str]
    min_score: int
    max_score: int
    passing_score: int
    is_active: bool
    current_version_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    current_version: Optional[ScorecardVersionResponse] = None

    class Config:
        from_attributes = True