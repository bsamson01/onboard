from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import uuid
from app.database import Base, UUID, JSONB


class LoanApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"
    ACTIVE = "active"
    DEFAULTED = "defaulted"
    COMPLETED = "completed"


class CreditBand(str, Enum):
    AA = "AA"  # Excellent
    A = "A"    # Good
    B = "B"    # Fair
    C = "C"    # Poor
    D = "D"    # Very Poor


class LoanType(str, Enum):
    PERSONAL = "personal"
    BUSINESS = "business"
    EMERGENCY = "emergency"
    EDUCATION = "education"
    AGRICULTURE = "agriculture"
    MICROENTERPRISE = "microenterprise"


class DecisionType(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    OVERRIDE = "override"


class LoanApplication(Base):
    __tablename__ = "loan_applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    application_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Loan Details
    loan_type = Column(SQLEnum(LoanType), nullable=False)
    requested_amount = Column(Numeric(12, 2), nullable=False)
    approved_amount = Column(Numeric(12, 2))
    loan_purpose = Column(Text, nullable=False)
    repayment_period_months = Column(Integer, nullable=False)
    
    # Status and Processing
    status = Column(SQLEnum(LoanApplicationStatus), nullable=False, default=LoanApplicationStatus.DRAFT)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Assignment and Review
    assigned_officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    branch_code = Column(String(20))
    review_notes = Column(Text)
    internal_notes = Column(JSONB)
    
    # Decision Information
    decision_date = Column(DateTime(timezone=True))
    decision_made_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason = Column(Text)
    approval_conditions = Column(JSONB)
    
    # Risk Assessment
    risk_level = Column(String(20))  # low, medium, high, very_high
    risk_notes = Column(Text)
    requires_collateral = Column(Boolean, default=False)
    collateral_details = Column(JSONB)
    
    # External References
    bureau_reference = Column(String(100))
    external_score_reference = Column(String(100))
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    disbursed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer")
    assigned_officer = relationship("User", foreign_keys=[assigned_officer_id])
    decision_made_by = relationship("User", foreign_keys=[decision_made_by_id])
    credit_scores = relationship("CreditScore", back_populates="loan_application", cascade="all, delete-orphan")
    decisions = relationship("LoanDecision", back_populates="loan_application", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LoanApplication(id={self.id}, application_number={self.application_number}, status={self.status})>"
    
    @property
    def is_approved(self) -> bool:
        return self.status == LoanApplicationStatus.APPROVED
    
    @property
    def is_rejected(self) -> bool:
        return self.status == LoanApplicationStatus.REJECTED
    
    @property
    def is_active(self) -> bool:
        return self.status in [LoanApplicationStatus.ACTIVE, LoanApplicationStatus.DISBURSED]
    
    @property
    def latest_score(self):
        return max(self.credit_scores, key=lambda s: s.created_at) if self.credit_scores else None


class CreditScore(Base):
    __tablename__ = "credit_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_application_id = Column(UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    # Score Information
    score = Column(Integer, nullable=False)
    credit_band = Column(SQLEnum(CreditBand), nullable=False)
    score_version = Column(String(20), nullable=False)
    scorecard_name = Column(String(100))
    
    # Score Breakdown
    score_breakdown = Column(JSONB, nullable=False)  # Detailed scoring components
    contributing_factors = Column(JSONB)  # Factors that influenced the score
    risk_factors = Column(JSONB)  # Identified risk factors
    
    # Scoring Context
    scored_by = Column(String(50), default="system")  # system, manual, external
    scoring_method = Column(String(50))  # scorecard, ml_model, hybrid
    model_version = Column(String(20))
    
    # Validity and Overrides
    is_valid = Column(Boolean, default=True)
    is_overridden = Column(Boolean, default=False)
    override_reason = Column(Text)
    overridden_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    overridden_at = Column(DateTime(timezone=True))
    
    # External References
    bureau_score = Column(Integer)
    bureau_reference = Column(String(100))
    external_scores = Column(JSONB)  # Scores from other systems
    
    # Timestamps
    scored_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    loan_application = relationship("LoanApplication", back_populates="credit_scores")
    customer = relationship("Customer")
    overridden_by = relationship("User")
    
    def __repr__(self):
        return f"<CreditScore(id={self.id}, score={self.score}, band={self.credit_band})>"
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return self.expires_at < datetime.now(timezone.utc)
    
    @property
    def is_excellent(self) -> bool:
        return self.credit_band == CreditBand.AA
    
    @property
    def is_good(self) -> bool:
        return self.credit_band in [CreditBand.AA, CreditBand.A]
    
    @property
    def is_risky(self) -> bool:
        return self.credit_band in [CreditBand.C, CreditBand.D]


class LoanDecision(Base):
    __tablename__ = "loan_decisions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_application_id = Column(UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    
    # Decision Details
    decision = Column(String(20), nullable=False)  # approved, rejected, pending
    decision_type = Column(SQLEnum(DecisionType), nullable=False)
    confidence_score = Column(Numeric(5, 2))
    
    # Decision Logic
    decision_reason = Column(Text)
    decision_factors = Column(JSONB)  # Factors that led to the decision
    business_rules_applied = Column(JSONB)  # Rules that were triggered
    
    # Amounts and Terms
    recommended_amount = Column(Numeric(12, 2))
    recommended_term_months = Column(Integer)
    recommended_interest_rate = Column(Numeric(5, 2))
    conditions = Column(JSONB)  # Any conditions attached to approval
    
    # Decision Context
    made_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    review_level = Column(Integer, default=1)  # 1=officer, 2=supervisor, 3=manager
    requires_escalation = Column(Boolean, default=False)
    escalation_reason = Column(Text)
    
    # Override Information
    is_override = Column(Boolean, default=False)
    override_justification = Column(Text)
    original_decision = Column(String(20))
    override_approved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # References
    scorecard_reference = Column(String(100))
    policy_version = Column(String(20))
    
    # Timestamps
    decision_date = Column(DateTime(timezone=True), server_default=func.now())
    effective_date = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    loan_application = relationship("LoanApplication", back_populates="decisions")
    made_by = relationship("User", foreign_keys=[made_by_id])
    override_approved_by = relationship("User", foreign_keys=[override_approved_by_id])
    
    def __repr__(self):
        return f"<LoanDecision(id={self.id}, decision={self.decision}, type={self.decision_type})>"
    
    @property
    def is_approved(self) -> bool:
        return self.decision == "approved"
    
    @property
    def is_rejected(self) -> bool:
        return self.decision == "rejected"
    
    @property
    def is_pending(self) -> bool:
        return self.decision == "pending"


# Additional Status enum for the main models
class LoanStatus(str, Enum):
    """Alias for LoanApplicationStatus for backward compatibility"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"
    ACTIVE = "active"
    DEFAULTED = "defaulted"
    COMPLETED = "completed"