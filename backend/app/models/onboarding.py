from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import uuid
from app.database import Base


class OnboardingStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PENDING_DOCUMENTS = "pending_documents"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class DocumentType(str, Enum):
    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    PAYSLIP = "payslip"
    PROOF_OF_RESIDENCE = "proof_of_residence"
    BUSINESS_LICENSE = "business_license"
    OTHER = "other"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Personal Information
    customer_number = Column(String(50), unique=True, index=True)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    marital_status = Column(String(20))
    nationality = Column(String(50))
    id_number = Column(String(50), unique=True, index=True)
    id_type = Column(String(20), default="national_id")
    
    # Contact Information
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(50))
    
    # Alternative contact
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(20))
    emergency_contact_relationship = Column(String(50))
    
    # Employment Information
    employment_status = Column(String(50))
    employer_name = Column(String(255))
    job_title = Column(String(100))
    monthly_income = Column(Numeric(12, 2))
    employment_duration_months = Column(Integer)
    
    # Financial Information
    bank_name = Column(String(100))
    bank_account_number = Column(String(50))
    bank_account_type = Column(String(20))
    has_other_loans = Column(Boolean, default=False)
    other_loans_details = Column(JSONB)
    
    # Consent and Preferences
    consent_data_processing = Column(Boolean, default=False)
    consent_credit_check = Column(Boolean, default=False)
    consent_marketing = Column(Boolean, default=False)
    preferred_communication = Column(String(20), default="email")  # email, sms, phone
    
    # Status and Timestamps
    is_verified = Column(Boolean, default=False)
    verification_completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    onboarding_applications = relationship("OnboardingApplication", back_populates="customer", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, customer_number={self.customer_number})>"
    
    @property
    def full_address(self) -> str:
        parts = [self.address_line1, self.address_line2, self.city, self.state_province, self.postal_code, self.country]
        return ", ".join([part for part in parts if part])


class OnboardingApplication(Base):
    __tablename__ = "onboarding_applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    application_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Application Status
    status = Column(SQLEnum(OnboardingStatus), nullable=False, default=OnboardingStatus.DRAFT)
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=5)
    
    # Pre-scoring Information
    initial_score = Column(Integer)
    eligibility_result = Column(String(20))  # eligible, ineligible, pending
    scorecard_version = Column(String(20))
    score_breakdown = Column(JSONB)
    
    # Review Information
    assigned_officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    review_notes = Column(Text)
    rejection_reason = Column(Text)
    approved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    rejected_at = Column(DateTime(timezone=True))
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="onboarding_applications")
    assigned_officer = relationship("User", foreign_keys=[assigned_officer_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    steps = relationship("OnboardingStep", back_populates="application", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<OnboardingApplication(id={self.id}, application_number={self.application_number}, status={self.status})>"
    
    @property
    def progress_percentage(self) -> float:
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100
    
    @property
    def is_completed(self) -> bool:
        return self.status in [OnboardingStatus.APPROVED, OnboardingStatus.REJECTED, OnboardingStatus.COMPLETED]


class OnboardingStep(Base):
    __tablename__ = "onboarding_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("onboarding_applications.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(100), nullable=False)
    step_data = Column(JSONB)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    application = relationship("OnboardingApplication", back_populates="steps")
    
    def __repr__(self):
        return f"<OnboardingStep(id={self.id}, step_number={self.step_number}, completed={self.is_completed})>"


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    # Document Information
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    document_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    original_filename = Column(String(255))
    
    # Status and Processing
    status = Column(SQLEnum(DocumentStatus), nullable=False, default=DocumentStatus.UPLOADED)
    is_required = Column(Boolean, default=True)
    verification_notes = Column(Text)
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    verified_at = Column(DateTime(timezone=True))
    
    # OCR Results
    ocr_text = Column(Text)
    ocr_confidence = Column(Numeric(5, 2))
    extracted_data = Column(JSONB)
    
    # Expiry Information
    expires_at = Column(Date)
    expiry_reminder_sent = Column(Boolean, default=False)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="documents")
    verified_by = relationship("User")
    
    def __repr__(self):
        return f"<Document(id={self.id}, type={self.document_type}, status={self.status})>"
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        from datetime import date
        return self.expires_at < date.today()
    
    @property
    def file_extension(self) -> str:
        if self.original_filename:
            return self.original_filename.split('.')[-1].lower()
        return ""