from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import List, Optional
import uuid

from app.database import get_async_db
from app.models.user import User
from app.models.loan import LoanApplication, ApplicationStatus, ApplicationStatusHistory
from app.models.onboarding import Customer
from app.schemas.status import (
    StatusUpdateRequest, StatusCancelRequest, StatusHistoryResponse,
    ApplicationStatusResponse, ApplicationTimelineResponse, StatusTimelineEntry,
    AllowedTransitionsResponse, StatusUpdateResponse, CustomerApplicationsResponse,
    AdminApplicationsListResponse, StatusStatisticsResponse, ApplicationSummaryResponse,
    StatusDisplayInfo
)
from app.services.status_service import StatusService, StatusTransitionError
from app.core.auth import get_current_user, require_staff, require_loan_officer

router = APIRouter()
security = HTTPBearer()
status_service = StatusService()


@router.get("/applications/my", response_model=CustomerApplicationsResponse)
async def get_my_applications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get current user's applications with status information"""
    
    # Get customer record
    customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
    customer_result = await session.execute(customer_stmt)
    customer = customer_result.scalar()
    
    if not customer:
        return CustomerApplicationsResponse()
    
    # Get all applications for this customer
    apps_stmt = select(LoanApplication).where(
        LoanApplication.customer_id == customer.id
    ).order_by(desc(LoanApplication.created_at))
    
    apps_result = await session.execute(apps_stmt)
    applications = apps_result.scalars().all()
    
    active_application = None
    completed_applications = []
    
    for app in applications:
        status_display = status_service.get_status_display_info(app.status)
        
        app_summary = ApplicationSummaryResponse(
            id=app.id,
            application_number=app.application_number,
            status=app.status,
            status_display=StatusDisplayInfo(**status_display),
            loan_type=app.loan_type.value,
            requested_amount=float(app.requested_amount),
            created_at=app.created_at,
            submitted_at=app.submitted_at,
            last_updated=app.updated_at
        )
        
        if app.is_active and not active_application:
            active_application = app_summary
        elif app.is_completed:
            completed_applications.append(app_summary)
    
    # Check if customer can create new application
    can_create_new = not active_application
    
    return CustomerApplicationsResponse(
        active_application=active_application,
        completed_applications=completed_applications,
        can_create_new=can_create_new
    )


@router.get("/applications/{application_id}/status", response_model=ApplicationStatusResponse)
async def get_application_status(
    application_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get detailed status information for an application"""
    
    # Get application with related data
    stmt = select(LoanApplication).where(LoanApplication.id == application_id)
    result = await session.execute(stmt)
    application = result.scalar()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check access permissions
    if current_user.role.value == "customer":
        # Verify customer owns this application
        customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if not customer or str(application.customer_id) != str(customer.id):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get additional user information
    assigned_officer_name = None
    decision_made_by_name = None
    
    if application.assigned_officer:
        assigned_officer_name = application.assigned_officer.full_name
    
    if application.decision_made_by:
        decision_made_by_name = application.decision_made_by.full_name
    
    status_display = status_service.get_status_display_info(application.status)
    
    return ApplicationStatusResponse(
        application_id=application.id,
        application_number=application.application_number,
        status=application.status,
        status_display=StatusDisplayInfo(**status_display),
        can_be_cancelled=application.can_be_cancelled_by_customer,
        rejection_reason=application.rejection_reason,
        cancellation_reason=application.cancellation_reason,
        submitted_at=application.submitted_at,
        reviewed_at=application.reviewed_at,
        approved_at=application.approved_at,
        rejected_at=application.rejected_at,
        cancelled_at=application.cancelled_at,
        disbursed_at=application.disbursed_at,
        completed_at=application.completed_at,
        assigned_officer_name=assigned_officer_name,
        decision_made_by_name=decision_made_by_name
    )


@router.get("/applications/{application_id}/timeline", response_model=ApplicationTimelineResponse)
async def get_application_timeline(
    application_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get application status timeline and history"""
    
    # Get application
    stmt = select(LoanApplication).where(LoanApplication.id == application_id)
    result = await session.execute(stmt)
    application = result.scalar()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check access permissions
    if current_user.role.value == "customer":
        customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if not customer or str(application.customer_id) != str(customer.id):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get status history
    history = await status_service.get_status_history(session, application_id, current_user)
    
    # Build timeline
    timeline_statuses = [
        ApplicationStatus.IN_PROGRESS,
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.APPROVED,
        ApplicationStatus.AWAITING_DISBURSEMENT,
        ApplicationStatus.DONE
    ]
    
    timeline = []
    current_status = application.status
    
    for status in timeline_statuses:
        status_display = status_service.get_status_display_info(status)
        
        # Find timestamp for this status
        timestamp = None
        if status == ApplicationStatus.IN_PROGRESS:
            timestamp = application.created_at
        elif status == ApplicationStatus.SUBMITTED:
            timestamp = application.submitted_at
        elif status == ApplicationStatus.UNDER_REVIEW:
            timestamp = application.reviewed_at
        elif status == ApplicationStatus.APPROVED:
            timestamp = application.approved_at
        elif status == ApplicationStatus.AWAITING_DISBURSEMENT:
            timestamp = application.approved_at  # Use approval time as proxy
        elif status == ApplicationStatus.DONE:
            timestamp = application.completed_at
        
        is_current = status == current_status
        is_completed = timestamp is not None
        
        # Don't show future steps for rejected/cancelled applications
        if current_status in [ApplicationStatus.REJECTED, ApplicationStatus.CANCELLED]:
            if not is_completed and not is_current:
                continue
        
        timeline.append(StatusTimelineEntry(
            status=status,
            status_display=StatusDisplayInfo(**status_display),
            timestamp=timestamp,
            is_current=is_current,
            is_completed=is_completed
        ))
    
    # Convert history to response format
    history_responses = []
    for entry in history:
        changed_by_name = entry.changed_by.full_name if entry.changed_by else "System"
        
        history_responses.append(StatusHistoryResponse(
            id=entry.id,
            from_status=entry.from_status,
            to_status=entry.to_status,
            reason=entry.reason,
            notes=entry.notes,
            changed_by_id=entry.changed_by_id,
            changed_by_name=changed_by_name,
            change_type=entry.change_type,
            created_at=entry.created_at
        ))
    
    return ApplicationTimelineResponse(
        application_id=uuid.UUID(application_id),
        current_status=current_status,
        timeline=timeline,
        history=history_responses
    )


@router.get("/applications/{application_id}/allowed-transitions", response_model=AllowedTransitionsResponse)
async def get_allowed_transitions(
    application_id: str,
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Get allowed status transitions for staff users"""
    
    # Get application
    stmt = select(LoanApplication).where(LoanApplication.id == application_id)
    result = await session.execute(stmt)
    application = result.scalar()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get allowed transitions
    allowed_transitions = await status_service.get_allowed_transitions(
        application.status, 
        current_user.role.value
    )
    
    # Build transition info
    transition_info = {}
    for status in allowed_transitions:
        status_display = status_service.get_status_display_info(status)
        requires_reason = status in status_service.statuses_requiring_reason
        
        transition_info[status.value] = {
            "display": status_display,
            "requires_reason": requires_reason,
            "description": f"Transition to {status_display['label']}"
        }
    
    return AllowedTransitionsResponse(
        current_status=application.status,
        allowed_transitions=allowed_transitions,
        transition_info=transition_info
    )


@router.post("/applications/{application_id}/update-status", response_model=StatusUpdateResponse)
async def update_application_status(
    application_id: str,
    status_update: StatusUpdateRequest,
    request: Request,
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Update application status (staff only)"""
    
    try:
        # Update status
        application = await status_service.update_application_status(
            session=session,
            application_id=application_id,
            new_status=status_update.status,
            user=current_user,
            reason=status_update.reason,
            notes=status_update.notes,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Get the latest status history entry
        history_stmt = select(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == application_id
        ).order_by(desc(ApplicationStatusHistory.created_at)).limit(1)
        
        history_result = await session.execute(history_stmt)
        latest_history = history_result.scalar()
        
        # Build response
        status_display = status_service.get_status_display_info(application.status)
        
        app_response = ApplicationStatusResponse(
            application_id=application.id,
            application_number=application.application_number,
            status=application.status,
            status_display=StatusDisplayInfo(**status_display),
            can_be_cancelled=application.can_be_cancelled_by_customer,
            rejection_reason=application.rejection_reason,
            cancellation_reason=application.cancellation_reason,
            submitted_at=application.submitted_at,
            reviewed_at=application.reviewed_at,
            approved_at=application.approved_at,
            rejected_at=application.rejected_at,
            cancelled_at=application.cancelled_at,
            disbursed_at=application.disbursed_at,
            completed_at=application.completed_at
        )
        
        history_response = StatusHistoryResponse(
            id=latest_history.id,
            from_status=latest_history.from_status,
            to_status=latest_history.to_status,
            reason=latest_history.reason,
            notes=latest_history.notes,
            changed_by_id=latest_history.changed_by_id,
            changed_by_name=current_user.full_name,
            change_type=latest_history.change_type,
            created_at=latest_history.created_at
        )
        
        return StatusUpdateResponse(
            success=True,
            application=app_response,
            status_history_entry=history_response,
            message=f"Application status updated to {status_display['label']}"
        )
        
    except StatusTransitionError as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@router.post("/applications/{application_id}/cancel", response_model=StatusUpdateResponse)
async def cancel_application(
    application_id: str,
    cancel_request: StatusCancelRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Cancel application (customer action)"""
    
    try:
        # Cancel application
        application = await status_service.cancel_application(
            session=session,
            application_id=application_id,
            user=current_user,
            reason=cancel_request.reason,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Get the latest status history entry
        history_stmt = select(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == application_id
        ).order_by(desc(ApplicationStatusHistory.created_at)).limit(1)
        
        history_result = await session.execute(history_stmt)
        latest_history = history_result.scalar()
        
        # Build response
        status_display = status_service.get_status_display_info(application.status)
        
        app_response = ApplicationStatusResponse(
            application_id=application.id,
            application_number=application.application_number,
            status=application.status,
            status_display=StatusDisplayInfo(**status_display),
            can_be_cancelled=application.can_be_cancelled_by_customer,
            rejection_reason=application.rejection_reason,
            cancellation_reason=application.cancellation_reason,
            submitted_at=application.submitted_at,
            reviewed_at=application.reviewed_at,
            approved_at=application.approved_at,
            rejected_at=application.rejected_at,
            cancelled_at=application.cancelled_at,
            disbursed_at=application.disbursed_at,
            completed_at=application.completed_at
        )
        
        history_response = StatusHistoryResponse(
            id=latest_history.id,
            from_status=latest_history.from_status,
            to_status=latest_history.to_status,
            reason=latest_history.reason,
            notes=latest_history.notes,
            changed_by_id=latest_history.changed_by_id,
            changed_by_name=current_user.full_name,
            change_type=latest_history.change_type,
            created_at=latest_history.created_at
        )
        
        return StatusUpdateResponse(
            success=True,
            application=app_response,
            status_history_entry=history_response,
            message="Application has been cancelled successfully"
        )
        
    except StatusTransitionError as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel application: {str(e)}")


@router.get("/admin/applications", response_model=AdminApplicationsListResponse)
async def get_admin_applications_list(
    status: Optional[ApplicationStatus] = None,
    assigned_to_me: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Get applications list for admin/staff users"""
    
    # Build query
    stmt = select(LoanApplication)
    
    filters = {}
    
    if status:
        stmt = stmt.where(LoanApplication.status == status)
        filters["status"] = status.value
    
    if assigned_to_me:
        stmt = stmt.where(LoanApplication.assigned_officer_id == current_user.id)
        filters["assigned_to_me"] = True
    
    # Get total count
    count_stmt = select(func.count(LoanApplication.id))
    if status:
        count_stmt = count_stmt.where(LoanApplication.status == status)
    if assigned_to_me:
        count_stmt = count_stmt.where(LoanApplication.assigned_officer_id == current_user.id)
    
    count_result = await session.execute(count_stmt)
    total_count = count_result.scalar()
    
    # Get pending review count
    pending_stmt = select(func.count(LoanApplication.id)).where(
        LoanApplication.status.in_([ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW])
    )
    pending_result = await session.execute(pending_stmt)
    pending_review_count = pending_result.scalar()
    
    # Get applications with pagination
    stmt = stmt.order_by(desc(LoanApplication.updated_at)).limit(limit).offset(offset)
    result = await session.execute(stmt)
    applications = result.scalars().all()
    
    # Convert to response format
    app_summaries = []
    for app in applications:
        status_display = status_service.get_status_display_info(app.status)
        
        app_summaries.append(ApplicationSummaryResponse(
            id=app.id,
            application_number=app.application_number,
            status=app.status,
            status_display=StatusDisplayInfo(**status_display),
            loan_type=app.loan_type.value,
            requested_amount=float(app.requested_amount),
            created_at=app.created_at,
            submitted_at=app.submitted_at,
            last_updated=app.updated_at
        ))
    
    return AdminApplicationsListResponse(
        applications=app_summaries,
        total_count=total_count,
        pending_review_count=pending_review_count,
        filters_applied=filters
    )


@router.get("/admin/statistics", response_model=StatusStatisticsResponse)
async def get_status_statistics(
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Get application status statistics for admin dashboard"""
    
    # Total applications
    total_stmt = select(func.count(LoanApplication.id))
    total_result = await session.execute(total_stmt)
    total_applications = total_result.scalar()
    
    # By status
    by_status = {}
    for status in ApplicationStatus:
        status_stmt = select(func.count(LoanApplication.id)).where(LoanApplication.status == status)
        status_result = await session.execute(status_stmt)
        by_status[status.value] = status_result.scalar()
    
    # Pending review
    pending_review = by_status.get("submitted", 0) + by_status.get("under_review", 0)
    
    # Processing time and completion rate (simplified calculations)
    completed_statuses = [ApplicationStatus.DONE, ApplicationStatus.REJECTED, ApplicationStatus.CANCELLED]
    completed_stmt = select(LoanApplication).where(LoanApplication.status.in_(completed_statuses))
    completed_result = await session.execute(completed_stmt)
    completed_apps = completed_result.scalars().all()
    
    if completed_apps:
        total_processing_time = 0
        completed_count = 0
        
        for app in completed_apps:
            if app.submitted_at and app.completed_at:
                processing_time = (app.completed_at - app.submitted_at).days
                total_processing_time += processing_time
                completed_count += 1
        
        processing_time_avg_days = total_processing_time / completed_count if completed_count > 0 else 0
        completion_rate = (by_status.get("done", 0) / total_applications * 100) if total_applications > 0 else 0
    else:
        processing_time_avg_days = 0
        completion_rate = 0
    
    return StatusStatisticsResponse(
        total_applications=total_applications,
        by_status=by_status,
        pending_review=pending_review,
        processing_time_avg_days=processing_time_avg_days,
        completion_rate=completion_rate
    )