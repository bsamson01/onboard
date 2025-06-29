from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import List, Optional
import uuid
from datetime import datetime

from app.database import get_async_db
from app.models.user import User
from app.models.loan import LoanApplication, ApplicationStatus, ApplicationStatusHistory
from app.models.onboarding import Customer, OnboardingApplication, OnboardingStatus, OnboardingStep
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
    
    from app.models.onboarding import OnboardingApplication, OnboardingStatus
    
    # First try to find as loan application
    loan_stmt = select(LoanApplication).where(LoanApplication.id == application_id)
    loan_result = await session.execute(loan_stmt)
    loan_application = loan_result.scalar()
    
    if loan_application:
        # Handle loan application
        # Check access permissions
        if current_user.role.value == "customer":
            # Verify customer owns this application
            customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
            customer_result = await session.execute(customer_stmt)
            customer = customer_result.scalar()
            
            if not customer or str(loan_application.customer_id) != str(customer.id):
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Get additional user information
        assigned_officer_name = None
        decision_made_by_name = None
        
        if loan_application.assigned_officer:
            assigned_officer_name = loan_application.assigned_officer.full_name
        
        if loan_application.decision_made_by:
            decision_made_by_name = loan_application.decision_made_by.full_name
        
        status_display = status_service.get_status_display_info(loan_application.status)
        
        return ApplicationStatusResponse(
            application_id=loan_application.id,
            application_number=loan_application.application_number,
            status=loan_application.status,
            status_display=StatusDisplayInfo(**status_display),
            can_be_cancelled=loan_application.can_be_cancelled_by_customer,
            rejection_reason=loan_application.rejection_reason,
            cancellation_reason=loan_application.cancellation_reason,
            submitted_at=loan_application.submitted_at,
            reviewed_at=loan_application.reviewed_at,
            approved_at=loan_application.approved_at,
            rejected_at=loan_application.rejected_at,
            cancelled_at=loan_application.cancelled_at,
            disbursed_at=loan_application.disbursed_at,
            completed_at=loan_application.completed_at,
            assigned_officer_name=assigned_officer_name,
            decision_made_by_name=decision_made_by_name
        )
    
    # If not found as loan application, try onboarding application
    onboarding_stmt = select(OnboardingApplication).where(OnboardingApplication.id == application_id)
    onboarding_result = await session.execute(onboarding_stmt)
    onboarding_application = onboarding_result.scalar()
    
    if onboarding_application:
        # Handle onboarding application
        # Check access permissions
        if current_user.role.value == "customer":
            # Verify customer owns this application
            customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
            customer_result = await session.execute(customer_stmt)
            customer = customer_result.scalar()
            
            if not customer or str(onboarding_application.customer_id) != str(customer.id):
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Map OnboardingStatus to ApplicationStatus for display
        status_map = {
            OnboardingStatus.DRAFT: ApplicationStatus.IN_PROGRESS,
            OnboardingStatus.IN_PROGRESS: ApplicationStatus.IN_PROGRESS,
            OnboardingStatus.PENDING_DOCUMENTS: ApplicationStatus.IN_PROGRESS,
            OnboardingStatus.UNDER_REVIEW: ApplicationStatus.UNDER_REVIEW,
            OnboardingStatus.APPROVED: ApplicationStatus.APPROVED,
            OnboardingStatus.REJECTED: ApplicationStatus.REJECTED,
            OnboardingStatus.COMPLETED: ApplicationStatus.DONE
        }
        
        mapped_status = status_map.get(onboarding_application.status, ApplicationStatus.IN_PROGRESS)
        status_display = status_service.get_status_display_info(mapped_status)
        
        return ApplicationStatusResponse(
            application_id=onboarding_application.id,
            application_number=onboarding_application.application_number,
            status=mapped_status,
            status_display=StatusDisplayInfo(**status_display),
            can_be_cancelled=onboarding_application.status in [OnboardingStatus.UNDER_REVIEW],
            rejection_reason=onboarding_application.rejection_reason,
            cancellation_reason=onboarding_application.cancellation_reason,
            submitted_at=onboarding_application.submitted_at,
            reviewed_at=onboarding_application.reviewed_at,
            approved_at=onboarding_application.approved_at,
            rejected_at=onboarding_application.rejected_at,
            cancelled_at=onboarding_application.cancelled_at,
            disbursed_at=None,  # Onboarding apps don't have disbursement
            completed_at=onboarding_application.completed_at,
            assigned_officer_name=None,  # Onboarding apps don't have assignment yet
            decision_made_by_name=None
        )
    
    # If neither found
    raise HTTPException(status_code=404, detail="Application not found")


@router.get("/applications/{application_id}/timeline", response_model=ApplicationTimelineResponse)
async def get_application_timeline(
    application_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get application timeline and status history"""
    
    from app.models.onboarding import OnboardingApplication, OnboardingStatus, OnboardingStep
    
    # First try to find as loan application
    loan_stmt = select(LoanApplication).where(LoanApplication.id == application_id)
    loan_result = await session.execute(loan_stmt)
    loan_application = loan_result.scalar()
    
    if loan_application:
        # Handle loan application timeline
        # Check access permissions
        if current_user.role.value == "customer":
            customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
            customer_result = await session.execute(customer_stmt)
            customer = customer_result.scalar()
            
            if not customer or str(loan_application.customer_id) != str(customer.id):
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Get status history
        history_stmt = select(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == application_id
        ).order_by(ApplicationStatusHistory.created_at)
        
        history_result = await session.execute(history_stmt)
        history_entries = history_result.scalars().all()
        
        # Build timeline
        timeline_entries = []
        for entry in history_entries:
            from_status_display = status_service.get_status_display_info(entry.from_status)
            to_status_display = status_service.get_status_display_info(entry.to_status)
            
            timeline_entries.append(StatusTimelineEntry(
                status=entry.to_status,
                status_display=StatusDisplayInfo(**to_status_display),
                timestamp=entry.created_at,
                reason=entry.reason,
                notes=entry.notes,
                changed_by_name=entry.changed_by.full_name if entry.changed_by else "System",
                change_type=entry.change_type.value
            ))
        
        return ApplicationTimelineResponse(
            application_id=loan_application.id,
            application_number=loan_application.application_number,
            timeline=timeline_entries
        )
    
    # If not found as loan application, try onboarding application
    onboarding_stmt = select(OnboardingApplication).where(OnboardingApplication.id == application_id)
    onboarding_result = await session.execute(onboarding_stmt)
    onboarding_application = onboarding_result.scalar()
    
    if onboarding_application:
        # Handle onboarding application timeline
        # Check access permissions
        if current_user.role.value == "customer":
            customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
            customer_result = await session.execute(customer_stmt)
            customer = customer_result.scalar()
            
            if not customer or str(onboarding_application.customer_id) != str(customer.id):
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Get onboarding steps as timeline
        steps_stmt = select(OnboardingStep).where(
            OnboardingStep.application_id == application_id
        ).order_by(OnboardingStep.step_number)
        
        steps_result = await session.execute(steps_stmt)
        steps = steps_result.scalars().all()
        
        # Build timeline from steps
        timeline_entries = []
        for step in steps:
            if step.is_completed:
                # Map step to status for display
                step_status_map = {
                    1: ApplicationStatus.IN_PROGRESS,
                    2: ApplicationStatus.IN_PROGRESS,
                    3: ApplicationStatus.IN_PROGRESS,
                    4: ApplicationStatus.IN_PROGRESS,
                    5: ApplicationStatus.SUBMITTED
                }
                
                status = step_status_map.get(step.step_number, ApplicationStatus.IN_PROGRESS)
                status_display = status_service.get_status_display_info(status)
                
                timeline_entries.append(StatusTimelineEntry(
                    status=status,
                    status_display=StatusDisplayInfo(**status_display),
                    timestamp=step.completed_at,
                    reason=None,
                    notes=f"Completed {step.step_name}",
                    changed_by_name="Customer",
                    change_type="step_completion"
                ))
        
        # Add final application status if submitted
        if onboarding_application.status in [OnboardingStatus.UNDER_REVIEW, OnboardingStatus.APPROVED, OnboardingStatus.REJECTED, OnboardingStatus.COMPLETED]:
            status_map = {
                OnboardingStatus.UNDER_REVIEW: ApplicationStatus.UNDER_REVIEW,
                OnboardingStatus.APPROVED: ApplicationStatus.APPROVED,
                OnboardingStatus.REJECTED: ApplicationStatus.REJECTED,
                OnboardingStatus.COMPLETED: ApplicationStatus.DONE
            }
            
            mapped_status = status_map.get(onboarding_application.status, ApplicationStatus.IN_PROGRESS)
            status_display = status_service.get_status_display_info(mapped_status)
            
            timeline_entries.append(StatusTimelineEntry(
                status=mapped_status,
                status_display=StatusDisplayInfo(**status_display),
                timestamp=onboarding_application.submitted_at or onboarding_application.updated_at,
                reason=onboarding_application.rejection_reason or onboarding_application.cancellation_reason,
                notes=f"Application {onboarding_application.status.value.replace('_', ' ').title()}",
                changed_by_name="System",
                change_type="status_change"
            ))
        
        return ApplicationTimelineResponse(
            application_id=onboarding_application.id,
            application_number=onboarding_application.application_number,
            timeline=timeline_entries
        )
    
    # If neither found
    raise HTTPException(status_code=404, detail="Application not found")


@router.get("/applications/{application_id}/allowed-transitions", response_model=AllowedTransitionsResponse)
async def get_allowed_transitions(
    application_id: str,
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Get allowed status transitions for staff users"""
    
    # First try to find as loan application
    loan_stmt = select(LoanApplication).where(LoanApplication.id == application_id)
    loan_result = await session.execute(loan_stmt)
    loan_application = loan_result.scalar()
    
    if loan_application:
        # Handle loan application
        # Get allowed transitions
        allowed_transitions = await status_service.get_allowed_transitions(
            loan_application.status, 
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
            current_status=loan_application.status,
            allowed_transitions=allowed_transitions,
            transition_info=transition_info
        )
    
    # If not found as loan application, try onboarding application
    onboarding_stmt = select(OnboardingApplication).where(OnboardingApplication.id == application_id)
    onboarding_result = await session.execute(onboarding_stmt)
    onboarding_application = onboarding_result.scalar()
    
    if onboarding_application:
        # Handle onboarding application
        # Map OnboardingStatus to ApplicationStatus for transitions
        status_map = {
            OnboardingStatus.DRAFT: ApplicationStatus.IN_PROGRESS,
            OnboardingStatus.IN_PROGRESS: ApplicationStatus.IN_PROGRESS,
            OnboardingStatus.PENDING_DOCUMENTS: ApplicationStatus.IN_PROGRESS,
            OnboardingStatus.UNDER_REVIEW: ApplicationStatus.UNDER_REVIEW,
            OnboardingStatus.APPROVED: ApplicationStatus.APPROVED,
            OnboardingStatus.REJECTED: ApplicationStatus.REJECTED,
            OnboardingStatus.COMPLETED: ApplicationStatus.DONE
        }
        
        mapped_status = status_map.get(onboarding_application.status, ApplicationStatus.IN_PROGRESS)
        
        # Get allowed transitions for mapped status
        allowed_transitions = await status_service.get_allowed_transitions(
            mapped_status, 
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
            current_status=mapped_status,
            allowed_transitions=allowed_transitions,
            transition_info=transition_info
        )
    
    # If neither found
    raise HTTPException(status_code=404, detail="Application not found")


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
        # First try to find as loan application
        loan_stmt = select(LoanApplication).where(LoanApplication.id == application_id)
        loan_result = await session.execute(loan_stmt)
        loan_application = loan_result.scalar()
        
        if loan_application:
            # Handle loan application using existing service
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
        
        # If not found as loan application, try onboarding application
        onboarding_stmt = select(OnboardingApplication).where(OnboardingApplication.id == application_id)
        onboarding_result = await session.execute(onboarding_stmt)
        onboarding_application = onboarding_result.scalar()
        
        if onboarding_application:
            # Handle onboarding application
            # Map ApplicationStatus to OnboardingStatus
            status_map = {
                ApplicationStatus.IN_PROGRESS: OnboardingStatus.IN_PROGRESS,
                ApplicationStatus.SUBMITTED: OnboardingStatus.IN_PROGRESS,
                ApplicationStatus.UNDER_REVIEW: OnboardingStatus.UNDER_REVIEW,
                ApplicationStatus.APPROVED: OnboardingStatus.APPROVED,
                ApplicationStatus.REJECTED: OnboardingStatus.REJECTED,
                ApplicationStatus.CANCELLED: OnboardingStatus.REJECTED,  # Map to rejected for onboarding
                ApplicationStatus.DONE: OnboardingStatus.COMPLETED
            }
            
            new_onboarding_status = status_map.get(status_update.status)
            if not new_onboarding_status:
                raise HTTPException(status_code=400, detail=f"Status {status_update.status} is not valid for onboarding applications")
            
            # Store current status
            current_status = onboarding_application.status
            
            # Skip if status is the same
            if current_status == new_onboarding_status:
                # Map back to ApplicationStatus for response
                reverse_status_map = {v: k for k, v in status_map.items()}
                mapped_status = reverse_status_map.get(current_status, ApplicationStatus.IN_PROGRESS)
                status_display = status_service.get_status_display_info(mapped_status)
                
                return StatusUpdateResponse(
                    success=True,
                    application=ApplicationStatusResponse(
                        application_id=onboarding_application.id,
                        application_number=onboarding_application.application_number,
                        status=mapped_status,
                        status_display=StatusDisplayInfo(**status_display),
                        can_be_cancelled=False,
                        rejection_reason=onboarding_application.rejection_reason,
                        cancellation_reason=onboarding_application.cancellation_reason,
                        submitted_at=onboarding_application.submitted_at,
                        reviewed_at=onboarding_application.reviewed_at,
                        approved_at=onboarding_application.approved_at,
                        rejected_at=onboarding_application.rejected_at,
                        cancelled_at=onboarding_application.cancelled_at,
                        disbursed_at=None,
                        completed_at=onboarding_application.completed_at
                    ),
                    status_history_entry=None,
                    message=f"Application status is already {status_display['label']}"
                )
            
            # Update onboarding application status
            onboarding_application.status = new_onboarding_status
            
            # Update user state based on onboarding application status
            user_stmt = select(User).where(User.id == onboarding_application.customer.user_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar()
            
            if user:
                if new_onboarding_status == OnboardingStatus.UNDER_REVIEW:
                    user.user_state = 'onboarding'
                elif new_onboarding_status == OnboardingStatus.APPROVED:
                    user.user_state = 'onboarded'
                elif new_onboarding_status == OnboardingStatus.REJECTED:
                    user.user_state = 'registered'
            
            # Update specific timestamp fields based on status
            now = datetime.utcnow()
            if new_onboarding_status == OnboardingStatus.UNDER_REVIEW:
                onboarding_application.reviewed_at = now
                onboarding_application.assigned_officer_id = current_user.id
            elif new_onboarding_status == OnboardingStatus.APPROVED:
                onboarding_application.approved_at = now
                onboarding_application.decision_made_by_id = current_user.id
                onboarding_application.decision_date = now
            elif new_onboarding_status == OnboardingStatus.REJECTED:
                onboarding_application.rejected_at = now
                onboarding_application.decision_made_by_id = current_user.id
                onboarding_application.decision_date = now
                onboarding_application.rejection_reason = status_update.reason
            elif new_onboarding_status == OnboardingStatus.COMPLETED:
                onboarding_application.completed_at = now
            
            await session.commit()
            await session.refresh(onboarding_application)
            
            # Map back to ApplicationStatus for response
            reverse_status_map = {v: k for k, v in status_map.items()}
            mapped_status = reverse_status_map.get(new_onboarding_status, ApplicationStatus.IN_PROGRESS)
            status_display = status_service.get_status_display_info(mapped_status)
            
            return StatusUpdateResponse(
                success=True,
                application=ApplicationStatusResponse(
                    application_id=onboarding_application.id,
                    application_number=onboarding_application.application_number,
                    status=mapped_status,
                    status_display=StatusDisplayInfo(**status_display),
                    can_be_cancelled=False,
                    rejection_reason=onboarding_application.rejection_reason,
                    cancellation_reason=onboarding_application.cancellation_reason,
                    submitted_at=onboarding_application.submitted_at,
                    reviewed_at=onboarding_application.reviewed_at,
                    approved_at=onboarding_application.approved_at,
                    rejected_at=onboarding_application.rejected_at,
                    cancelled_at=onboarding_application.cancelled_at,
                    disbursed_at=None,
                    completed_at=onboarding_application.completed_at
                ),
                status_history_entry=None,  # Onboarding apps don't have status history table
                message=f"Application status updated to {status_display['label']}"
            )
        
        # If neither found
        raise HTTPException(status_code=404, detail="Application not found")
        
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
        # First try to find as loan application
        loan_stmt = select(LoanApplication).where(LoanApplication.id == application_id)
        loan_result = await session.execute(loan_stmt)
        loan_application = loan_result.scalar()
        
        if loan_application:
            # Handle loan application using existing service
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
        
        # If not found as loan application, try onboarding application
        onboarding_stmt = select(OnboardingApplication).where(OnboardingApplication.id == application_id)
        onboarding_result = await session.execute(onboarding_stmt)
        onboarding_application = onboarding_result.scalar()
        
        if onboarding_application:
            # Handle onboarding application cancellation
            # Check if user is the customer (via customer relationship)
            if current_user.role.value == "customer":
                customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
                customer_result = await session.execute(customer_stmt)
                customer = customer_result.scalar()
                
                if not customer or str(onboarding_application.customer_id) != str(customer.id):
                    raise HTTPException(status_code=403, detail="You can only cancel your own applications")
            
            # Check if application can be cancelled
            cancellable_statuses = [OnboardingStatus.DRAFT, OnboardingStatus.IN_PROGRESS, OnboardingStatus.PENDING_DOCUMENTS]
            if onboarding_application.status not in cancellable_statuses:
                raise StatusTransitionError(f"Application in status '{onboarding_application.status}' cannot be cancelled")
            
            # Update onboarding application status
            onboarding_application.status = OnboardingStatus.REJECTED
            onboarding_application.cancellation_reason = cancel_request.reason
            onboarding_application.cancelled_at = datetime.utcnow()
            
            # Update user state to 'registered' when application is cancelled
            user_stmt = select(User).where(User.id == onboarding_application.customer.user_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar()
            if user:
                user.user_state = 'registered'
            
            await session.commit()
            await session.refresh(onboarding_application)
            
            # Map to ApplicationStatus for response
            status_display = status_service.get_status_display_info(ApplicationStatus.CANCELLED)
            
            return StatusUpdateResponse(
                success=True,
                application=ApplicationStatusResponse(
                    application_id=onboarding_application.id,
                    application_number=onboarding_application.application_number,
                    status=ApplicationStatus.CANCELLED,
                    status_display=StatusDisplayInfo(**status_display),
                    can_be_cancelled=False,
                    rejection_reason=onboarding_application.rejection_reason,
                    cancellation_reason=onboarding_application.cancellation_reason,
                    submitted_at=onboarding_application.submitted_at,
                    reviewed_at=onboarding_application.reviewed_at,
                    approved_at=onboarding_application.approved_at,
                    rejected_at=onboarding_application.rejected_at,
                    cancelled_at=onboarding_application.cancelled_at,
                    disbursed_at=None,
                    completed_at=onboarding_application.completed_at
                ),
                status_history_entry=None,  # Onboarding apps don't have status history table
                message="Application has been cancelled successfully"
            )
        
        # If neither found
        raise HTTPException(status_code=404, detail="Application not found")
        
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
    application_type: Optional[str] = None,  # 'onboarding' or 'loan' or None for all
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Get applications list for admin/staff users. Returns both onboarding and loan applications ready for review."""
    from app.models.onboarding import OnboardingApplication, OnboardingStatus
    from app.models.loan import LoanApplication
    from app.schemas.status import ApplicationSummaryResponse, StatusDisplayInfo
    from app.services.status_service import status_service
    from sqlalchemy import desc, or_

    all_applications = []

    # Only fetch onboarding applications if not filtering for loan applications
    if application_type != 'loan':
        # Onboarding applications ready for review (UNDER_REVIEW status)
        onboarding_conditions = [OnboardingApplication.status == OnboardingStatus.UNDER_REVIEW]
        
        # Apply status filter for onboarding
        if status == ApplicationStatus.UNDER_REVIEW:
            pass  # Already filtered above
        elif status == ApplicationStatus.APPROVED:
            onboarding_conditions = [OnboardingApplication.status == OnboardingStatus.APPROVED]
        elif status == ApplicationStatus.REJECTED:
            onboarding_conditions = [OnboardingApplication.status == OnboardingStatus.REJECTED]
        elif status == ApplicationStatus.DONE:
            onboarding_conditions = [OnboardingApplication.status == OnboardingStatus.COMPLETED]
        elif status == ApplicationStatus.IN_PROGRESS:
            onboarding_conditions = [OnboardingApplication.status.in_([
                OnboardingStatus.DRAFT, OnboardingStatus.IN_PROGRESS, OnboardingStatus.PENDING_DOCUMENTS
            ])]
        elif status is None:
            # Include all onboarding applications for review
            onboarding_conditions = [OnboardingApplication.status.in_([
                OnboardingStatus.UNDER_REVIEW, OnboardingStatus.APPROVED, OnboardingStatus.REJECTED, OnboardingStatus.COMPLETED
            ])]

        onboarding_stmt = select(OnboardingApplication).where(*onboarding_conditions)
        
        # Apply assignment filter for onboarding
        if assigned_to_me:
            onboarding_stmt = onboarding_stmt.where(OnboardingApplication.assigned_officer_id == current_user.id)
        
        onboarding_stmt = onboarding_stmt.order_by(desc(OnboardingApplication.updated_at))
        onboarding_result = await session.execute(onboarding_stmt)
        onboarding_applications = onboarding_result.scalars().all()

        # Map OnboardingStatus to ApplicationStatus for display
        onboarding_status_map = {
            OnboardingStatus.DRAFT: ApplicationStatus.IN_PROGRESS,
            OnboardingStatus.IN_PROGRESS: ApplicationStatus.IN_PROGRESS,
            OnboardingStatus.PENDING_DOCUMENTS: ApplicationStatus.IN_PROGRESS,
            OnboardingStatus.UNDER_REVIEW: ApplicationStatus.UNDER_REVIEW,
            OnboardingStatus.APPROVED: ApplicationStatus.APPROVED,
            OnboardingStatus.REJECTED: ApplicationStatus.REJECTED,
            OnboardingStatus.COMPLETED: ApplicationStatus.DONE
        }

        for app in onboarding_applications:
            mapped_status = onboarding_status_map.get(app.status, ApplicationStatus.IN_PROGRESS)
            status_display = status_service.get_status_display_info(mapped_status)
            all_applications.append({
                'app': app,
                'type': 'onboarding',
                'updated_at': app.updated_at,
                'summary': ApplicationSummaryResponse(
                    id=app.id,
                    application_number=app.application_number,
                    status=mapped_status,
                    status_display=StatusDisplayInfo(**status_display),
                    loan_type="Onboarding",
                    requested_amount=0.0,
                    created_at=app.created_at,
                    submitted_at=app.submitted_at,
                    last_updated=app.updated_at
                )
            })

    # Only fetch loan applications if not filtering for onboarding applications
    if application_type != 'onboarding':
        # Loan applications ready for review (SUBMITTED and UNDER_REVIEW statuses)
        loan_conditions = []
        
        # Apply status filter for loans
        if status == ApplicationStatus.SUBMITTED:
            loan_conditions = [LoanApplication.status == ApplicationStatus.SUBMITTED]
        elif status == ApplicationStatus.UNDER_REVIEW:
            loan_conditions = [LoanApplication.status == ApplicationStatus.UNDER_REVIEW]
        elif status == ApplicationStatus.APPROVED:
            loan_conditions = [LoanApplication.status == ApplicationStatus.APPROVED]
        elif status == ApplicationStatus.REJECTED:
            loan_conditions = [LoanApplication.status == ApplicationStatus.REJECTED]
        elif status == ApplicationStatus.AWAITING_DISBURSEMENT:
            loan_conditions = [LoanApplication.status == ApplicationStatus.AWAITING_DISBURSEMENT]
        elif status == ApplicationStatus.DONE:
            loan_conditions = [LoanApplication.status == ApplicationStatus.DONE]
        elif status == ApplicationStatus.CANCELLED:
            loan_conditions = [LoanApplication.status == ApplicationStatus.CANCELLED]
        elif status == ApplicationStatus.IN_PROGRESS:
            loan_conditions = [LoanApplication.status == ApplicationStatus.IN_PROGRESS]
        elif status is None:
            # Include all loan applications for review/management
            loan_conditions = [LoanApplication.status.in_([
                ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW, 
                ApplicationStatus.APPROVED, ApplicationStatus.REJECTED,
                ApplicationStatus.AWAITING_DISBURSEMENT, ApplicationStatus.DONE, ApplicationStatus.CANCELLED
            ])]
        else:
            loan_conditions = [LoanApplication.status.in_([
                ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW
            ])]

        loan_stmt = select(LoanApplication).where(*loan_conditions)
        
        # Apply assignment filter for loans
        if assigned_to_me:
            loan_stmt = loan_stmt.where(LoanApplication.assigned_officer_id == current_user.id)
        
        loan_stmt = loan_stmt.order_by(desc(LoanApplication.updated_at))
        loan_result = await session.execute(loan_stmt)
        loan_applications = loan_result.scalars().all()

        for app in loan_applications:
            status_display = status_service.get_status_display_info(app.status)
            all_applications.append({
                'app': app,
                'type': 'loan',
                'updated_at': app.updated_at,
                'summary': ApplicationSummaryResponse(
                    id=app.id,
                    application_number=app.application_number,
                    status=app.status,
                    status_display=StatusDisplayInfo(**status_display),
                    loan_type=str(app.loan_type.value) if hasattr(app.loan_type, 'value') else str(app.loan_type),
                    requested_amount=float(app.requested_amount),
                    created_at=app.created_at,
                    submitted_at=app.submitted_at,
                    last_updated=app.updated_at
                )
            })

    # Sort all applications by update time
    all_applications.sort(key=lambda x: x['updated_at'], reverse=True)
    
    # Apply pagination
    start_idx = offset
    end_idx = start_idx + limit
    paginated_applications = all_applications[start_idx:end_idx]
    app_summaries = [item['summary'] for item in paginated_applications]

    # Count pending review applications (UNDER_REVIEW for onboarding, SUBMITTED + UNDER_REVIEW for loans)
    pending_review_count = sum(1 for app in all_applications 
                              if app['summary'].status in [ApplicationStatus.UNDER_REVIEW, ApplicationStatus.SUBMITTED])

    return AdminApplicationsListResponse(
        applications=app_summaries,
        total_count=len(all_applications),
        pending_review_count=pending_review_count,
        filters_applied={
            "status": status.value if status else None, 
            "assigned_to_me": assigned_to_me,
            "application_type": application_type
        }
    )


@router.get("/admin/statistics", response_model=StatusStatisticsResponse)
async def get_status_statistics(
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Get application status statistics for admin dashboard"""
    
    from app.models.onboarding import OnboardingApplication, OnboardingStatus
    
    # Total applications (both types)
    loan_total_stmt = select(func.count(LoanApplication.id))
    onboarding_total_stmt = select(func.count(OnboardingApplication.id))
    
    loan_total_result = await session.execute(loan_total_stmt)
    onboarding_total_result = await session.execute(onboarding_total_stmt)
    total_applications = loan_total_result.scalar() + onboarding_total_result.scalar()
    
    # By status (combine both application types)
    by_status = {}
    for status in ApplicationStatus:
        loan_status_stmt = select(func.count(LoanApplication.id)).where(LoanApplication.status == status)
        loan_status_result = await session.execute(loan_status_stmt)
        loan_count = loan_status_result.scalar()
        
        # Map ApplicationStatus to OnboardingStatus for onboarding applications
        onboarding_status_map = {
            ApplicationStatus.IN_PROGRESS: OnboardingStatus.IN_PROGRESS,
            ApplicationStatus.UNDER_REVIEW: OnboardingStatus.UNDER_REVIEW,
            ApplicationStatus.APPROVED: OnboardingStatus.APPROVED,
            ApplicationStatus.REJECTED: OnboardingStatus.REJECTED,
            ApplicationStatus.DONE: OnboardingStatus.COMPLETED
        }
        
        onboarding_count = 0
        if status in onboarding_status_map:
            onboarding_status_stmt = select(func.count(OnboardingApplication.id)).where(
                OnboardingApplication.status == onboarding_status_map[status]
            )
            onboarding_status_result = await session.execute(onboarding_status_stmt)
            onboarding_count = onboarding_status_result.scalar()
        
        by_status[status.value] = loan_count + onboarding_count
    
    # Pending review (both types)
    pending_loan_stmt = select(func.count(LoanApplication.id)).where(
        LoanApplication.status.in_([ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW])
    )
    pending_onboarding_stmt = select(func.count(OnboardingApplication.id)).where(
        OnboardingApplication.status.in_([OnboardingStatus.UNDER_REVIEW])
    )
    
    pending_loan_result = await session.execute(pending_loan_stmt)
    pending_onboarding_result = await session.execute(pending_onboarding_stmt)
    pending_review = pending_loan_result.scalar() + pending_onboarding_result.scalar()
    
    # Processing time and completion rate (simplified calculations)
    completed_loan_statuses = [ApplicationStatus.DONE, ApplicationStatus.REJECTED, ApplicationStatus.CANCELLED]
    completed_onboarding_statuses = [OnboardingStatus.COMPLETED, OnboardingStatus.REJECTED]
    
    completed_loan_stmt = select(LoanApplication).where(LoanApplication.status.in_(completed_loan_statuses))
    completed_onboarding_stmt = select(OnboardingApplication).where(OnboardingApplication.status.in_(completed_onboarding_statuses))
    
    completed_loan_result = await session.execute(completed_loan_stmt)
    completed_onboarding_result = await session.execute(completed_onboarding_stmt)
    completed_loan_apps = completed_loan_result.scalars().all()
    completed_onboarding_apps = completed_onboarding_result.scalars().all()
    
    all_completed_apps = list(completed_loan_apps) + list(completed_onboarding_apps)
    
    if all_completed_apps:
        total_processing_time = 0
        completed_count = 0
        
        for app in all_completed_apps:
            if hasattr(app, 'submitted_at') and hasattr(app, 'completed_at') and app.submitted_at and app.completed_at:
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