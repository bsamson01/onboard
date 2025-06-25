from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class ScoreResult(Base):
    """Results of scorecard evaluation for an applicant."""
    __tablename__ = "score_results"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # References
    scorecard_id = Column(Integer, ForeignKey("scorecard_configs.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("scorecard_versions.id"), nullable=False)
    applicant_id = Column(String(100), index=True, nullable=False)  # External applicant reference
    
    # Score results
    total_score = Column(Integer, nullable=False)
    letter_grade = Column(String(5))  # AA, A+, A, B+, B, C+, C, D
    eligibility = Column(Boolean, nullable=False)
    
    # Detailed breakdown (stored as JSON)
    factor_scores = Column(JSON)  # Individual factor scores and reasoning
    breakdown = Column(JSON)      # Human-readable breakdown
    
    # Processing metadata
    processing_time_ms = Column(Integer)
    data_completeness = Column(Float)  # Percentage of required data provided
    confidence_score = Column(Float)   # Algorithm confidence in the result
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    scorecard = relationship("ScorecardConfig", back_populates="evaluations")
    version = relationship("ScorecardVersion", back_populates="evaluations")
    evaluation_logs = relationship("EvaluationLog", back_populates="score_result")


class EvaluationLog(Base):
    """Detailed audit log for scorecard evaluations."""
    __tablename__ = "evaluation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # References
    score_result_id = Column(Integer, ForeignKey("score_results.id"), nullable=False)
    
    # Request details
    request_id = Column(String(100), index=True)  # For tracing requests
    user_id = Column(String(100))  # Who triggered the evaluation
    source_system = Column(String(100))  # onboarding, loan_app, etc.
    
    # Input data (anonymized/sanitized for audit)
    input_data_hash = Column(String(64))  # Hash of input data for integrity
    data_sources = Column(JSON)  # Which data sources were used
    
    # Processing details
    evaluation_steps = Column(JSON)  # Step-by-step evaluation process
    warnings = Column(JSON)  # Any warnings during evaluation
    errors = Column(JSON)    # Any errors that occurred
    
    # Performance metrics
    processing_time_ms = Column(Integer)
    memory_usage_mb = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    score_result = relationship("ScoreResult", back_populates="evaluation_logs")