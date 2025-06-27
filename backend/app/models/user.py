from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import uuid
from datetime import datetime, timedelta
from app.database import Base, UUID, JSONB


class UserRole(str, Enum):
    ADMIN = "admin"
    RISK_OFFICER = "risk_officer"
    LOAN_OFFICER = "loan_officer"
    SUPPORT = "support"
    CUSTOMER = "customer"


class UserState(str, Enum):
    REGISTERED = "registered"
    ONBOARDED = "onboarded"
    OUTDATED = "outdated"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # MFA fields
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    backup_codes = Column(JSONB)
    
    # Profile fields
    profile_picture_url = Column(String(500))
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # User State Management
    user_state = Column(SQLEnum(UserState), nullable=False, default=UserState.REGISTERED)
    onboarding_completed_at = Column(DateTime(timezone=True))
    last_profile_update = Column(DateTime(timezone=True))
    profile_expiry_date = Column(DateTime(timezone=True))
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    @property
    def is_risk_officer(self) -> bool:
        return self.role == UserRole.RISK_OFFICER
    
    @property
    def is_loan_officer(self) -> bool:
        return self.role == UserRole.LOAN_OFFICER
    
    @property
    def is_support(self) -> bool:
        return self.role == UserRole.SUPPORT
    
    @property
    def is_customer(self) -> bool:
        return self.role == UserRole.CUSTOMER
    
    @property
    def can_access_admin(self) -> bool:
        return self.role in [UserRole.ADMIN]
    
    @property
    def can_access_risk(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.RISK_OFFICER]
    
    @property
    def can_access_loans(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.RISK_OFFICER, UserRole.LOAN_OFFICER]
    
    @property
    def can_create_loans(self) -> bool:
        """Check if user can create new loan applications."""
        if self.role != UserRole.CUSTOMER:
            return False
        return self.user_state == UserState.ONBOARDED
    
    @property
    def needs_profile_update(self) -> bool:
        """Check if user profile needs to be updated."""
        if not self.profile_expiry_date:
            return False
        return datetime.utcnow() > self.profile_expiry_date
    
    @property
    def is_profile_outdated(self) -> bool:
        """Check if user profile is outdated (more than 1 year old)."""
        return self.user_state == UserState.OUTDATED
    
    @property
    def profile_completion_percentage(self) -> float:
        """Calculate profile completion percentage."""
        if self.user_state == UserState.REGISTERED:
            return 0.0
        elif self.user_state == UserState.ONBOARDED:
            return 100.0
        else:  # OUTDATED
            return 50.0  # Profile exists but needs updating


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), unique=True, index=True)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(255), index=True)
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    additional_data = Column(JSONB)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, resource_type={self.resource_type})>"
    
    # Index for efficient querying by timestamp and user
    __table_args__ = (
        {"comment": "Immutable audit log for all system changes"},
    )


class UserRoleHistory(Base):
    __tablename__ = "user_role_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    old_role = Column(String(50))
    new_role = Column(String(50), nullable=False)
    changed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    reason = Column(Text)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    changed_by = relationship("User", foreign_keys=[changed_by_id])
    
    def __repr__(self):
        return f"<UserRoleHistory(id={self.id}, user_id={self.user_id}, old_role={self.old_role}, new_role={self.new_role})>"