from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.database import get_async_db
from app.models.user import User
from app.models.loan import LoanApplication, CreditScore, LoanDecision, ApplicationStatus
from app.models.onboarding import Customer, OnboardingApplication, OnboardingStatus
from app.schemas.loan import (
    LoanApplicationCreate, LoanApplicationResponse, LoanApplicationUpdate, 
    LoanApplicationListResponse, LoanApplicationSubmitRequest, LoanApplicationSubmitResponse,
    LoanDecisionCreate, ApplicationStatusResponse, LoanEligibilityCheckResponse,
    CreditScoreResponse, LoanDecisionResponse, BulkLoanApplicationsRequest, BulkLoanApplicationsResponse
)
from app.core.auth import get_current_user, require_staff, require_admin
from app.services.scorecard_service import ScorecardService
from app.services.status_service import status_service
from app.services.audit_service import AuditService

router = APIRouter()


async def get_customer_for_user(user: User, session: AsyncSession) -> Customer:
    """Get customer profile for the current user"""
    stmt = select(Customer).where(Customer.user_id == user.id)
    result = await session.execute(stmt)
    customer = result.scalar()
    if not customer:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Customer profile not found. Please complete onboarding first."
        )
    return customer


async def verify_onboarding_complete(customer: Customer, session: AsyncSession) -> None:
    """Verify that the customer has completed onboarding"""
    stmt = select(OnboardingApplication).where(
        and_(
            OnboardingApplication.customer_id == customer.id,
            OnboardingApplication.status == OnboardingStatus.APPROVED
        )
    )
    result = await session.execute(stmt)
    onboarding_app = result.scalar()
    if not onboarding_app:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="You must complete and get approval for onboarding before applying for a loan."
        )


async def check_active_loan_applications(customer: Customer, session: AsyncSession, exclude_application_id: Optional[uuid.UUID] = None) -> None:
    """Check if customer has any active loan applications"""
    active_statuses = [
        ApplicationStatus.IN_PROGRESS, 
        ApplicationStatus.SUBMITTED, 
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.AWAITING_DISBURSEMENT
    ]
    conditions = [
        LoanApplication.customer_id == customer.id,
        LoanApplication.status.in_(active_statuses)
    ]
    if exclude_application_id:
        conditions.append(func.replace(LoanApplication.id, '-', '') != exclude_application_id.hex)
    stmt = select(LoanApplication).where(and_(*conditions))
    result = await session.execute(stmt)
    active_app = result.scalar()
    
    if active_app:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"You already have an active loan application ({active_app.application_number}). "
                   f"Please wait for it to be processed or contact support."
        )


async def get_loan_application_for_user(
    application_id: uuid.UUID, 
    user: User, 
    session: AsyncSession
) -> LoanApplication:
    """Get loan application that belongs to the current user"""
    customer = await get_customer_for_user(user, session)
    print(f"DEBUG: application_id={application_id}, user_id={user.id}, customer_id={customer.id}")
    # Normalize UUID for SQLite (remove dashes)
    stmt = select(LoanApplication).options(
        selectinload(LoanApplication.credit_scores),
        selectinload(LoanApplication.decisions),
        selectinload(LoanApplication.customer)
    ).where(
        and_(
            func.replace(LoanApplication.id, '-', '') == application_id.hex,
            LoanApplication.customer_id == customer.id
        )
    )
    result = await session.execute(stmt)
    application = result.scalar()
    if not application:
        print(f"DEBUG: No application found for application_id={application_id} and customer_id={customer.id}")
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Loan application not found."
        )
    return application


@router.post("/eligibility-check", response_model=LoanEligibilityCheckResponse)
async def check_loan_eligibility(
    application_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Check if user is eligible to apply for or update a loan application"""
    try:
        customer = await get_customer_for_user(current_user, session)
        await verify_onboarding_complete(customer, session)
        if application_id:
            application = await get_loan_application_for_user(application_id, current_user, session)
            await check_active_loan_applications(customer, session, exclude_application_id=application_id)
            # Allow update if not in a terminal state
            editable_statuses = [
                ApplicationStatus.IN_PROGRESS,
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.UNDER_REVIEW,
                ApplicationStatus.AWAITING_DISBURSEMENT
            ]
            if application.status not in editable_statuses:
                return LoanEligibilityCheckResponse(
                    is_eligible=False,
                    eligibility_reasons=[f"Application is not in a modifiable state: {application.status.value}"],
                    max_loan_amount=None,
                    recommended_loan_types=[],
                    requirements=["Application must not be cancelled, rejected, or completed to update"]
                )
        else:
            await check_active_loan_applications(customer, session)
        # Basic eligibility check
        eligibility_reasons = ["Onboarding completed", "No active loan applications"]
        is_eligible = True
        max_loan_amount = 50000  # Basic default
        recommended_loan_types = ["personal", "business", "emergency"]
        requirements = []
        return LoanEligibilityCheckResponse(
            is_eligible=is_eligible,
            eligibility_reasons=eligibility_reasons,
            max_loan_amount=max_loan_amount,
            recommended_loan_types=recommended_loan_types,
            requirements=requirements
        )
    except HTTPException as exc:
        print('HTTPException', exc.detail)
        return LoanEligibilityCheckResponse(
            is_eligible=False,
            eligibility_reasons=[str(exc.detail)],
            max_loan_amount=None,
            recommended_loan_types=[],
            requirements=["Complete customer onboarding", "Resolve any pending applications"]
        )


@router.post("/applications", response_model=LoanApplicationResponse)
async def create_loan_application(
    loan_data: LoanApplicationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Create a new loan application"""
    # Validate customer eligibility
    customer = await get_customer_for_user(current_user, session)
    await verify_onboarding_complete(customer, session)
    await check_active_loan_applications(customer, session)
    
    # Generate application number
    current_time = datetime.now(timezone.utc)
    app_number = f"LOAN{current_time.strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
    
    # Create loan application
    loan_application = LoanApplication(
        customer_id=customer.id,
        application_number=app_number,
        loan_type=loan_data.loan_type,
        requested_amount=loan_data.requested_amount,
        loan_purpose=loan_data.loan_purpose,
        repayment_period_months=loan_data.repayment_period_months,
        status=ApplicationStatus.IN_PROGRESS
    )
    
    if loan_data.additional_notes:
        loan_application.internal_notes = {"customer_notes": loan_data.additional_notes}
    
    session.add(loan_application)
    await session.commit()
    await session.refresh(loan_application)
    
    # Load with relationships for response
    stmt = select(LoanApplication).options(
        selectinload(LoanApplication.credit_scores),
        selectinload(LoanApplication.decisions)
    ).where(LoanApplication.id == loan_application.id)
    
    result = await session.execute(stmt)
    application = result.scalar()
    
    return application


@router.get("/applications", response_model=LoanApplicationListResponse)
async def get_loan_applications(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get loan applications for the current user"""
    customer = await get_customer_for_user(current_user, session)
    
    # Build query
    query = select(LoanApplication).options(
        selectinload(LoanApplication.credit_scores),
        selectinload(LoanApplication.decisions)
    ).where(LoanApplication.customer_id == customer.id)
    
    # Apply status filter
    if status_filter:
        try:
            status_enum = ApplicationStatus(status_filter)
            query = query.where(LoanApplication.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    # Apply pagination
    offset = (page - 1) * size
    query = query.order_by(desc(LoanApplication.created_at)).offset(offset).limit(size)
    
    # Get total count
    count_query = select(LoanApplication).where(LoanApplication.customer_id == customer.id)
    if status_filter:
        count_query = count_query.where(LoanApplication.status == ApplicationStatus(status_filter))
    
    count_result = await session.execute(count_query)
    total = len(count_result.all())
    
    # Get applications
    result = await session.execute(query)
    applications = result.scalars().all()
    
    # Prepare applications with required nested fields
    def get_latest(items, date_attr):
        return max(items, key=lambda x: getattr(x, date_attr)) if items else None

    serialized_applications = []
    for app in applications:
        latest_score = get_latest(app.credit_scores, 'scored_at')
        latest_decision = get_latest(app.decisions, 'decision_date')
        app_dict = app.__dict__.copy()
        app_dict['latest_credit_score'] = CreditScoreResponse.model_validate(latest_score) if latest_score else None
        app_dict['latest_decision'] = LoanDecisionResponse.model_validate(latest_decision) if latest_decision else None
        # Add computed properties
        app_dict['is_approved'] = app.is_approved
        app_dict['is_rejected'] = app.is_rejected
        app_dict['is_cancelled'] = app.is_cancelled
        app_dict['is_active'] = app.is_active
        app_dict['is_completed'] = app.is_completed
        app_dict['can_be_cancelled_by_customer'] = app.can_be_cancelled_by_customer
        serialized_applications.append(LoanApplicationResponse.model_validate(app_dict))

    pages = (total + size - 1) // size
    
    return LoanApplicationListResponse(
        applications=serialized_applications,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/applications/{application_id}", response_model=LoanApplicationResponse)
async def get_loan_application(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    print('get_loan_application', application_id)
    """Get a specific loan application"""
    application = await get_loan_application_for_user(application_id, current_user, session)
    # Prepare nested fields and computed properties as in the list endpoint
    def get_latest(items, date_attr):
        return max(items, key=lambda x: getattr(x, date_attr)) if items else None
    from app.schemas.loan import CreditScoreResponse, LoanDecisionResponse, LoanApplicationResponse
    latest_score = get_latest(application.credit_scores, 'scored_at')
    latest_decision = get_latest(application.decisions, 'decision_date')
    app_dict = application.__dict__.copy()
    app_dict['latest_credit_score'] = CreditScoreResponse.model_validate(latest_score) if latest_score else None
    app_dict['latest_decision'] = LoanDecisionResponse.model_validate(latest_decision) if latest_decision else None
    app_dict['is_approved'] = application.is_approved
    app_dict['is_rejected'] = application.is_rejected
    app_dict['is_cancelled'] = application.is_cancelled
    app_dict['is_active'] = application.is_active
    app_dict['is_completed'] = application.is_completed
    app_dict['can_be_cancelled_by_customer'] = application.can_be_cancelled_by_customer
    return LoanApplicationResponse.model_validate(app_dict)


@router.put("/applications/{application_id}", response_model=LoanApplicationResponse)
async def update_loan_application(
    application_id: uuid.UUID,
    loan_data: LoanApplicationUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Update a loan application (only allowed if in progress)"""
    application = await get_loan_application_for_user(application_id, current_user, session)
    # Check if application can be updated
    if application.status != ApplicationStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Loan application can only be updated while in progress."
        )
    # Update fields
    update_data = loan_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(application, field):
            setattr(application, field, value)
    application.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(application)
    # Serialize as in get_loan_application
    def get_latest(items, date_attr):
        return max(items, key=lambda x: getattr(x, date_attr)) if items else None
    from app.schemas.loan import CreditScoreResponse, LoanDecisionResponse, LoanApplicationResponse
    latest_score = get_latest(application.credit_scores, 'scored_at')
    latest_decision = get_latest(application.decisions, 'decision_date')
    app_dict = application.__dict__.copy()
    app_dict['latest_credit_score'] = CreditScoreResponse.model_validate(latest_score) if latest_score else None
    app_dict['latest_decision'] = LoanDecisionResponse.model_validate(latest_decision) if latest_decision else None
    app_dict['is_approved'] = application.is_approved
    app_dict['is_rejected'] = application.is_rejected
    app_dict['is_cancelled'] = application.is_cancelled
    app_dict['is_active'] = application.is_active
    app_dict['is_completed'] = application.is_completed
    app_dict['can_be_cancelled_by_customer'] = application.can_be_cancelled_by_customer
    return LoanApplicationResponse.model_validate(app_dict)


@router.post("/applications/{application_id}/submit", response_model=LoanApplicationSubmitResponse)
async def submit_loan_application(
    application_id: uuid.UUID,
    submit_request: LoanApplicationSubmitRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Submit loan application for review"""
    application = await get_loan_application_for_user(application_id, current_user, session)
    # Check if application can be submitted
    if application.status != ApplicationStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Only applications in progress can be submitted."
        )
    # Update application status
    application.status = ApplicationStatus.SUBMITTED
    application.submitted_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(application)
    # Serialize as in get_loan_application
    def get_latest(items, date_attr):
        return max(items, key=lambda x: getattr(x, date_attr)) if items else None
    from app.schemas.loan import CreditScoreResponse, LoanDecisionResponse, LoanApplicationResponse
    latest_score = get_latest(application.credit_scores, 'scored_at')
    latest_decision = get_latest(application.decisions, 'decision_date')
    app_dict = application.__dict__.copy()
    app_dict['latest_credit_score'] = CreditScoreResponse.model_validate(latest_score) if latest_score else None
    app_dict['latest_decision'] = LoanDecisionResponse.model_validate(latest_decision) if latest_decision else None
    app_dict['is_approved'] = application.is_approved
    app_dict['is_rejected'] = application.is_rejected
    app_dict['is_cancelled'] = application.is_cancelled
    app_dict['is_active'] = application.is_active
    app_dict['is_completed'] = application.is_completed
    app_dict['can_be_cancelled_by_customer'] = application.can_be_cancelled_by_customer
    next_steps = [
        "Your application has been submitted for review",
        "Our team will review your application within 2-3 business days",
        "You will be notified of the decision via email and SMS",
        "If approved, loan disbursement will be processed within 1-2 business days"
    ]
    return LoanApplicationSubmitResponse(
        message="Loan application submitted successfully",
        application=LoanApplicationResponse.model_validate(app_dict),
        next_steps=next_steps
    )


@router.delete("/applications/{application_id}")
async def cancel_loan_application(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Cancel a loan application"""
    application = await get_loan_application_for_user(application_id, current_user, session)
    
    # Check if application can be cancelled
    if not application.can_be_cancelled_by_customer:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="This application cannot be cancelled at its current stage."
        )
    
    # Update status
    application.status = ApplicationStatus.CANCELLED
    application.cancelled_at = datetime.now(timezone.utc)
    application.cancellation_reason = "Cancelled by customer"
    
    await session.commit()
    
    return {"message": "Loan application cancelled successfully"}


@router.get("/applications/{application_id}/status", response_model=ApplicationStatusResponse)
async def get_application_status(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get detailed status information for a loan application"""
    application = await get_loan_application_for_user(application_id, current_user, session)
    
    # Create basic status response
    status_display = {
        "label": application.status.value.replace("_", " ").title(),
        "color": "blue" if application.status == ApplicationStatus.IN_PROGRESS else "green",
        "description": f"Application is currently {application.status.value.replace('_', ' ')}"
    }
    
    return ApplicationStatusResponse(
        status=application.status,
        status_display=status_display,
        can_be_cancelled=application.can_be_cancelled_by_customer,
        can_be_submitted=application.status == ApplicationStatus.IN_PROGRESS,
        next_possible_statuses=["submitted"] if application.status == ApplicationStatus.IN_PROGRESS else [],
        status_history=[]
    )


@router.get("/applications/{application_id}/credit-score", response_model=CreditScoreResponse)
async def get_loan_credit_score(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get credit score for a loan application"""
    application = await get_loan_application_for_user(application_id, current_user, session)
    
    if not application.latest_score:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No credit score available for this application"
        )
    
    return application.latest_score


# Staff/Admin endpoints
@router.get("/admin/applications", response_model=LoanApplicationListResponse)
async def get_all_loan_applications(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    assigned_officer_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Get all loan applications (staff/admin only)"""
    query = select(LoanApplication).options(
        selectinload(LoanApplication.credit_scores),
        selectinload(LoanApplication.decisions),
        selectinload(LoanApplication.customer)
    )
    
    # Apply filters
    if status_filter:
        try:
            status_enum = ApplicationStatus(status_filter)
            query = query.where(LoanApplication.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    if assigned_officer_id:
        query = query.where(LoanApplication.assigned_officer_id == assigned_officer_id)
    
    # Apply pagination
    offset = (page - 1) * size
    query = query.order_by(desc(LoanApplication.created_at)).offset(offset).limit(size)
    
    # Get total count
    count_query = select(LoanApplication)
    if status_filter:
        count_query = count_query.where(LoanApplication.status == ApplicationStatus(status_filter))
    if assigned_officer_id:
        count_query = count_query.where(LoanApplication.assigned_officer_id == assigned_officer_id)
    
    count_result = await session.execute(count_query)
    total = len(count_result.all())
    
    # Get applications
    result = await session.execute(query)
    applications = result.scalars().all()
    
    pages = (total + size - 1) // size
    
    return LoanApplicationListResponse(
        applications=applications,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/admin/applications/{application_id}/decisions", response_model=LoanDecisionResponse)
async def create_loan_decision(
    application_id: uuid.UUID,
    decision_data: LoanDecisionCreate,
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Create a loan decision (staff/admin only)"""
    # Get application
    stmt = select(LoanApplication).where(LoanApplication.id == application_id)
    result = await session.execute(stmt)
    application = result.scalar()
    
    if not application:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Loan application not found"
        )
    
    # Check if application is in reviewable state
    if application.status not in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Application is not in a reviewable state"
        )
    
    # Create decision
    decision = LoanDecision(
        loan_application_id=application.id,
        decision=decision_data.decision,
        decision_type="manual",
        decision_reason=decision_data.decision_reason,
        recommended_amount=decision_data.recommended_amount,
        recommended_term_months=decision_data.recommended_term_months,
        recommended_interest_rate=decision_data.recommended_interest_rate,
        conditions=decision_data.conditions,
        requires_escalation=decision_data.requires_escalation,
        escalation_reason=decision_data.escalation_reason,
        made_by_id=current_user.id,
        review_level=1
    )
    
    session.add(decision)
    
    # Update application based on decision
    if decision_data.decision == "approved":
        application.status = ApplicationStatus.APPROVED
        application.approved_at = datetime.now(timezone.utc)
        application.approved_amount = decision_data.recommended_amount
        application.decision_made_by_id = current_user.id
        application.decision_date = datetime.now(timezone.utc)
    elif decision_data.decision == "rejected":
        application.status = ApplicationStatus.REJECTED
        application.rejected_at = datetime.now(timezone.utc)
        application.rejection_reason = decision_data.decision_reason
        application.decision_made_by_id = current_user.id
        application.decision_date = datetime.now(timezone.utc)
    
    await session.commit()
    await session.refresh(decision)
    
    return decision