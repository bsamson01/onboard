from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import uuid
from app.database import Base, UUID, JSONB


class AlertType(str, Enum):
    PAYMENT_OVERDUE = "payment_overdue"
    RISK_SCORE_CHANGE = "risk_score_change"
    DOCUMENT_EXPIRY = "document_expiry"
    SYSTEM_ERROR = "system_error"
    FRAUD_DETECTION = "fraud_detection"
    CUSTOMER_INACTIVITY = "customer_inactivity"
    LOAN_DEFAULT_RISK = "loan_default_risk"
    COMPLIANCE_ISSUE = "compliance_issue"
    APPLICATION_ESCALATION = "application_escalation"
    SCORECARD_UPDATE = "scorecard_update"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH_NOTIFICATION = "push_notification"


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Alert Classification
    alert_type = Column(SQLEnum(AlertType), nullable=False, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, default=AlertSeverity.MEDIUM)
    status = Column(SQLEnum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE, index=True)
    
    # Alert Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    description = Column(Text)
    action_required = Column(Text)
    
    # Alert Context
    resource_type = Column(String(50))  # customer, loan_application, user, system
    resource_id = Column(String(255), index=True)
    
    # Targeting
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    target_role = Column(String(50))  # Target specific role if not user-specific
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Alert Rules and Triggers
    trigger_conditions = Column(JSONB)  # Conditions that triggered this alert
    business_rule_id = Column(String(100))
    trigger_data = Column(JSONB)  # Data that caused the trigger
    
    # Processing Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    read_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    resolved_at = Column(DateTime(timezone=True))
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolution_notes = Column(Text)
    
    # Escalation
    escalation_level = Column(Integer, default=0)
    escalated_at = Column(DateTime(timezone=True))
    escalated_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    escalation_reason = Column(Text)
    
    # External Integration
    webhook_sent = Column(Boolean, default=False)
    webhook_response = Column(JSONB)
    external_reference = Column(String(255))
    
    # Expiry and Auto-Resolution
    expires_at = Column(DateTime(timezone=True))
    auto_resolve = Column(Boolean, default=False)
    auto_resolved_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    target_user = relationship("User", foreign_keys=[target_user_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    read_by = relationship("User", foreign_keys=[read_by_id])
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    escalated_to = relationship("User", foreign_keys=[escalated_to_id])
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type}, severity={self.severity}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        return self.status == AlertStatus.ACTIVE
    
    @property
    def is_resolved(self) -> bool:
        return self.status == AlertStatus.RESOLVED
    
    @property
    def is_critical(self) -> bool:
        return self.severity == AlertSeverity.CRITICAL
    
    @property
    def is_high_priority(self) -> bool:
        return self.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return self.expires_at < datetime.now(timezone.utc)
    
    @property
    def days_since_created(self) -> int:
        from datetime import datetime, timezone
        return (datetime.now(timezone.utc) - self.created_at).days
    
    @property
    def requires_action(self) -> bool:
        return self.action_required is not None and self.status == AlertStatus.ACTIVE


class AlertNotification(Base):
    __tablename__ = "alert_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    
    # Notification Details
    channel = Column(SQLEnum(AlertChannel), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    recipient_email = Column(String(255))
    recipient_phone = Column(String(20))
    
    # Message Content
    subject = Column(String(255))
    message_body = Column(Text)
    template_used = Column(String(100))
    
    # Delivery Status
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True))
    delivery_status = Column(String(50), default="pending")  # pending, sent, delivered, failed, bounced
    
    # Delivery Attempts
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_attempt_at = Column(DateTime(timezone=True))
    next_retry_at = Column(DateTime(timezone=True))
    
    # Response Tracking
    is_opened = Column(Boolean, default=False)
    opened_at = Column(DateTime(timezone=True))
    is_clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime(timezone=True))
    
    # Error Information
    error_message = Column(Text)
    error_code = Column(String(50))
    
    # External References
    external_id = Column(String(255))  # ID from email/SMS provider
    webhook_data = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    alert = relationship("Alert")
    recipient = relationship("User")
    
    def __repr__(self):
        return f"<AlertNotification(id={self.id}, channel={self.channel}, status={self.delivery_status})>"
    
    @property
    def is_delivered(self) -> bool:
        return self.delivery_status == "delivered"
    
    @property
    def is_failed(self) -> bool:
        return self.delivery_status == "failed"
    
    @property
    def can_retry(self) -> bool:
        return self.attempts < self.max_attempts and self.delivery_status in ["pending", "failed"]
    
    @property
    def is_engagement_tracked(self) -> bool:
        return self.channel in [AlertChannel.EMAIL, AlertChannel.PUSH_NOTIFICATION]


class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule Definition
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    
    # Rule Logic
    conditions = Column(JSONB, nullable=False)  # Rule conditions in JSON format
    triggers = Column(JSONB)  # What events trigger this rule
    
    # Rule Configuration
    is_active = Column(Boolean, default=True)
    target_roles = Column(JSONB)  # Which roles should receive these alerts
    channels = Column(JSONB, default=["in_app"])  # Which channels to use
    
    # Processing Rules
    debounce_minutes = Column(Integer, default=0)  # Minimum time between same alerts
    auto_resolve_hours = Column(Integer)  # Auto-resolve after X hours
    escalation_minutes = Column(Integer)  # Escalate if not acknowledged in X minutes
    
    # Template Configuration
    title_template = Column(String(500))
    message_template = Column(Text)
    email_template = Column(String(100))
    sms_template = Column(String(100))
    
    # Business Context
    business_priority = Column(Integer, default=5)  # 1-10 priority scale
    compliance_related = Column(Boolean, default=False)
    customer_facing = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    last_modified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    last_modified_by = relationship("User", foreign_keys=[last_modified_by_id])
    
    def __repr__(self):
        return f"<AlertRule(id={self.id}, name={self.name}, type={self.alert_type})>"
    
    @property
    def is_compliance_critical(self) -> bool:
        return self.compliance_related and self.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]