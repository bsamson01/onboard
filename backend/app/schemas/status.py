from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.models.loan import ApplicationStatus


class StatusUpdateRequest(BaseModel):
    """Request schema for updating application status"""
    status: ApplicationStatus = Field(..., description="New status to transition to")
    reason: Optional[str] = Field(None, description="Reason for status change (required for rejected/cancelled)")
    notes: Optional[str] = Field(None, description="Additional notes for the status change")

    class Config:
        use_enum_values = True


class StatusCancelRequest(BaseModel):
    """Request schema for cancelling application"""
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for cancellation")


class StatusHistoryResponse(BaseModel):
    """Response schema for status history entry"""
    id: uuid.UUID
    from_status: Optional[ApplicationStatus]
    to_status: ApplicationStatus
    reason: Optional[str]
    notes: Optional[str]
    changed_by_id: uuid.UUID
    changed_by_name: Optional[str] = None
    change_type: str
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class StatusDisplayInfo(BaseModel):
    """Status display information for UI"""
    label: str = Field(..., description="Human-readable status label")
    color: str = Field(..., description="Color code for UI display")
    description: str = Field(..., description="Status description")


class ApplicationStatusResponse(BaseModel):
    """Response schema for application status information"""
    application_id: uuid.UUID
    application_number: str
    status: ApplicationStatus
    status_display: StatusDisplayInfo
    can_be_cancelled: bool
    rejection_reason: Optional[str] = None
    cancellation_reason: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    disbursed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_officer_name: Optional[str] = None
    decision_made_by_name: Optional[str] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class StatusTimelineEntry(BaseModel):
    """Timeline entry for status tracking"""
    status: ApplicationStatus
    status_display: StatusDisplayInfo
    timestamp: Optional[datetime]
    is_current: bool
    is_completed: bool
    description: Optional[str] = None

    class Config:
        use_enum_values = True


class ApplicationTimelineResponse(BaseModel):
    """Response schema for application status timeline"""
    application_id: uuid.UUID
    current_status: ApplicationStatus
    timeline: List[StatusTimelineEntry]
    history: List[StatusHistoryResponse]

    class Config:
        use_enum_values = True


class AllowedTransitionsResponse(BaseModel):
    """Response schema for allowed status transitions"""
    current_status: ApplicationStatus
    allowed_transitions: List[ApplicationStatus]
    transition_info: Dict[str, Dict[str, Any]]  # Maps status to requirements/info

    class Config:
        use_enum_values = True


class StatusUpdateResponse(BaseModel):
    """Response schema for status update operation"""
    success: bool
    application: ApplicationStatusResponse
    status_history_entry: StatusHistoryResponse
    message: str


class ApplicationSummaryResponse(BaseModel):
    """Summary response for application with status info"""
    id: uuid.UUID
    application_number: str
    status: ApplicationStatus
    status_display: StatusDisplayInfo
    loan_type: str
    requested_amount: float
    created_at: datetime
    submitted_at: Optional[datetime] = None
    last_updated: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class CustomerApplicationsResponse(BaseModel):
    """Response schema for customer's applications list"""
    active_application: Optional[ApplicationSummaryResponse] = None
    completed_applications: List[ApplicationSummaryResponse] = []
    can_create_new: bool = True

    class Config:
        use_enum_values = True


class AdminApplicationsListResponse(BaseModel):
    """Response schema for admin applications list"""
    applications: List[ApplicationSummaryResponse]
    total_count: int
    pending_review_count: int
    filters_applied: Dict[str, Any]

    class Config:
        use_enum_values = True


class StatusStatisticsResponse(BaseModel):
    """Response schema for status statistics"""
    total_applications: int
    by_status: Dict[str, int]
    pending_review: int
    processing_time_avg_days: float
    completion_rate: float

    class Config:
        use_enum_values = True