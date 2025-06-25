from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from typing import Dict, Any
import uuid


class ScorecardConfig(Base):
    """Main scorecard configuration for an MFI."""
    __tablename__ = "scorecard_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    mfi_id = Column(String(50), index=True, nullable=False)  # Microfinance Institution ID
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Scorecard settings
    min_score = Column(Integer, default=300)
    max_score = Column(Integer, default=850)
    passing_score = Column(Integer, default=600)
    
    # Status and versioning
    is_active = Column(Boolean, default=True)
    current_version_id = Column(Integer, ForeignKey("scorecard_versions.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    versions = relationship("ScorecardVersion", back_populates="scorecard", foreign_keys="ScorecardVersion.scorecard_id")
    current_version = relationship("ScorecardVersion", foreign_keys=[current_version_id], post_update=True)
    evaluations = relationship("ScoreResult", back_populates="scorecard")


class ScorecardVersion(Base):
    """Versioned scorecard configuration for audit trail and rollback."""
    __tablename__ = "scorecard_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    scorecard_id = Column(Integer, ForeignKey("scorecard_configs.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    # Version metadata
    description = Column(Text)
    is_active = Column(Boolean, default=False)
    
    # Scorecard configuration (stored as JSON)
    config_data = Column(JSON)  # Stores the complete configuration
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))
    
    # Relationships
    scorecard = relationship("ScorecardConfig", back_populates="versions", foreign_keys=[scorecard_id])
    scoring_factors = relationship("ScoringFactor", back_populates="version")
    evaluations = relationship("ScoreResult", back_populates="version")


class ScoringFactor(Base):
    """Individual scoring factors within a scorecard version."""
    __tablename__ = "scoring_factors"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(Integer, ForeignKey("scorecard_versions.id"), nullable=False)
    
    # Factor definition
    name = Column(String(200), nullable=False)  # e.g., "Monthly Income"
    code = Column(String(50), nullable=False)   # e.g., "monthly_income"
    description = Column(Text)
    category = Column(String(100))  # e.g., "Financial", "Demographic", "Behavioral"
    
    # Scoring configuration
    weight = Column(Float, default=1.0)  # Factor weight in overall score
    data_type = Column(String(20), default="numeric")  # numeric, categorical, boolean
    
    # Rule configuration (stored as JSON for flexibility)
    rules = Column(JSON)  # Contains scoring rules and thresholds
    
    # Factor metadata
    is_required = Column(Boolean, default=True)
    min_value = Column(Float)
    max_value = Column(Float)
    default_points = Column(Integer, default=0)  # Points if data unavailable
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    version = relationship("ScorecardVersion", back_populates="scoring_factors")