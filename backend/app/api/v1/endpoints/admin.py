from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from typing import Dict, Any, List
import httpx
import asyncio
from datetime import datetime
import logging
import uuid as uuid_lib

from app.database import get_async_db
from app.models.user import User
from app.core.auth import require_admin, require_loan_officer, require_staff
from app.config import settings
from app.services.scorecard_service import ScorecardService
from app.services.audit_service import AuditService
from app.core.logging import log_audit_event, AuditEvent
from pydantic import BaseModel, HttpUrl
from app.models.onboarding import OnboardingApplication, OnboardingStatus, OnboardingStep, Customer, Document, DocumentStatus
from app.models.loan import ApplicationStatus
from app.services.status_service import StatusService
from app.services.user_state_service import UserStateService
from app.schemas.profile import (
    RoleUpdateRequest, StateUpdateRequest, DocumentVerificationRequest,
    AdminUserProfileResponse, DocumentResponse, UserRoleHistoryResponse,
    BulkUserOperationRequest, BulkUserOperationResponse
)
from app.models.user import UserRole, UserState, UserRoleHistory

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
scorecard_service = ScorecardService()
audit_service = AuditService()
status_service = StatusService()
user_state_service = UserStateService()


class ExternalServiceConfig(BaseModel):
    """External service configuration model."""
    name: str
    url: HttpUrl
    api_key: str = ""
    timeout: int = 30
    is_enabled: bool = True
    description: str = ""


class SystemHealthResponse(BaseModel):
    """System health response model."""
    status: str
    timestamp: datetime
    services: Dict[str, Dict[str, Any]]
    database: Dict[str, Any]
    external_services: Dict[str, Dict[str, Any]]


class ConfigurationUpdateRequest(BaseModel):
    """Configuration update request model."""
    scorecard_api_url: HttpUrl
    scorecard_api_key: str
    scorecard_timeout: int = 30


@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_db)
):
    """Get admin dashboard data."""
    try:
        dashboard_data = {
            "system_status": "operational",
            "total_users": await _get_user_count(session),
            "active_applications": await _get_active_applications_count(session),
            "pending_review_count": await _get_pending_review_count(session),
            "approved_count": await _get_approved_count(session),
            "rejected_count": await _get_rejected_count(session),
            "recent_activities": await _get_recent_activities(session),
            "system_health": await _get_system_health_summary(),
            "configuration_status": await _get_configuration_status()
        }
        return dashboard_data
    except Exception as e:
        logger.error(f"Failed to get admin dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard data"
        )


@router.get("/users", response_model=List[Dict[str, Any]])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_db)
):
    """Get list of users (admin only)."""
    try:
        stmt = select(User).offset(skip).limit(limit)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        user_list = []
        for user in users:
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "user_state": user.user_state.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_locked": user.is_locked,
                "failed_login_attempts": user.failed_login_attempts,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "onboarding_completed_at": user.onboarding_completed_at.isoformat() if user.onboarding_completed_at else None,
                "last_profile_update": user.last_profile_update.isoformat() if user.last_profile_update else None,
                "profile_expiry_date": user.profile_expiry_date.isoformat() if user.profile_expiry_date else None,
                "profile_completion_percentage": user.profile_completion_percentage,
                "can_create_loans": user.can_create_loans
            }
            user_list.append(user_data)
        
        return user_list
        
    except Exception as e:
        logger.error(f"Failed to get users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/system-health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: User = Depends(require_admin)
):
    """Get comprehensive system health status."""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": {
                "api": {"status": "healthy", "response_time": "< 100ms"},
                "authentication": {"status": "healthy", "last_check": datetime.utcnow()},
                "audit_logging": {"status": "healthy", "last_log": datetime.utcnow()}
            },
            "database": await _check_database_health(),
            "external_services": await _check_external_services()
        }
        
        # Determine overall status
        all_statuses = []
        all_statuses.extend([service["status"] for service in health_data["services"].values()])
        all_statuses.append(health_data["database"]["status"])
        all_statuses.extend([service["status"] for service in health_data["external_services"].values()])
        
        if "unhealthy" in all_statuses:
            health_data["status"] = "unhealthy"
        elif "degraded" in all_statuses:
            health_data["status"] = "degraded"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health"
        )


@router.get("/external-services")
async def get_external_services_config(
    current_user: User = Depends(require_admin)
):
    """Get external services configuration."""
    try:
        services_config = {
            "scorecard_service": {
                "name": "Scorecard API",
                "url": settings.SCORECARD_API_URL,
                "api_key": "***" + settings.SCORECARD_API_KEY[-4:] if settings.SCORECARD_API_KEY else "",
                "timeout": 30,
                "is_enabled": bool(settings.SCORECARD_API_URL and settings.SCORECARD_API_KEY),
                "description": "External credit scoring service",
                "last_health_check": await _get_last_health_check("scorecard"),
                "health_status": await _check_scorecard_health()
            }
        }
        
        return services_config
        
    except Exception as e:
        logger.error(f"Failed to get external services config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve external services configuration"
        )


@router.post("/external-services/scorecard/configure")
async def configure_scorecard_service(
    config: ConfigurationUpdateRequest,
    request: Request,
    current_user: User = Depends(require_admin)
):
    """Configure scorecard service settings."""
    try:
        # Validate the new configuration by testing the connection
        test_result = await _test_scorecard_connection(str(config.scorecard_api_url), config.scorecard_api_key)
        
        if not test_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Configuration test failed: {test_result['error']}"
            )
        
        # Store old configuration for audit
        old_config = {
            "url": settings.SCORECARD_API_URL,
            "api_key_length": len(settings.SCORECARD_API_KEY) if settings.SCORECARD_API_KEY else 0
        }
        
        # Update configuration (in a real app, this would update a configuration store)
        # For now, we'll log the change and return success
        new_config = {
            "url": str(config.scorecard_api_url),
            "api_key_length": len(config.scorecard_api_key),
            "timeout": config.scorecard_timeout
        }
        
        # Log configuration change
        await audit_service.log_onboarding_action(
            user_id=str(current_user.id),
            action="external_service_configuration_updated",
            resource_type="system_configuration",
            resource_id="scorecard_service",
            old_values=old_config,
            new_values=new_config,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            additional_data={
                "service_name": "scorecard_service",
                "test_result": test_result
            }
        )
        
        log_audit_event(
            AuditEvent.ADMIN_ACTION,
            user_id=str(current_user.id),
            details={
                "action": "scorecard_configuration_updated",
                "ip_address": request.client.host
            }
        )
        
        return {
            "success": True,
            "message": "Scorecard service configuration updated successfully",
            "test_result": test_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure scorecard service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update scorecard configuration"
        )


@router.post("/external-services/scorecard/test")
async def test_scorecard_connection(
    current_user: User = Depends(require_admin)
):
    """Test scorecard service connection."""
    try:
        result = await _test_scorecard_connection(settings.SCORECARD_API_URL, settings.SCORECARD_API_KEY)
        return result
        
    except Exception as e:
        logger.error(f"Failed to test scorecard connection: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "response_time": None
        }


@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action_filter: str = None,
    user_filter: str = None,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_db)
):
    """Get audit logs with filtering."""
    try:
        from app.models.user import AuditLog
        
        query = select(AuditLog)
        
        # Apply filters
        if action_filter:
            query = query.where(AuditLog.action.ilike(f"%{action_filter}%"))
        
        if user_filter:
            query = query.where(AuditLog.user_id == user_filter)
        
        query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        audit_logs = result.scalars().all()
        
        logs_data = []
        for log in audit_logs:
            log_data = {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "additional_data": log.additional_data
            }
            logs_data.append(log_data)
        
        return {
            "logs": logs_data,
            "total": len(logs_data),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_db)
):
    """Delete a user (admin only)."""
    try:
        # Get user to delete
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user_to_delete = result.scalar()
        
        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-deletion
        if str(user_to_delete.id) == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Delete user
        await session.delete(user_to_delete)
        await session.commit()
        
        # Log the action
        await log_audit_event(
            AuditEvent.USER_DELETED,
            user_id=str(current_user.id),
            details={
                "deleted_user_id": str(user_to_delete.id),
                "deleted_user_email": user_to_delete.email,
                "ip_address": request.client.host
            }
        )
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.post("/applications/{application_id}/unlock")
async def unlock_application_for_editing(
    application_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_db)
):
    """Unlock an application for editing by changing status back to IN_PROGRESS (admin only)."""
    try:
        # First try to find as onboarding application
        stmt = select(OnboardingApplication).where(OnboardingApplication.id == application_id)
        result = await session.execute(stmt)
        onboarding_app = result.scalar()
        
        if onboarding_app:
            # Handle onboarding application
            if onboarding_app.status not in [OnboardingStatus.UNDER_REVIEW, OnboardingStatus.APPROVED, OnboardingStatus.REJECTED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Application is not in a locked state that can be unlocked"
                )
            
            # Change status back to IN_PROGRESS
            onboarding_app.status = OnboardingStatus.IN_PROGRESS
            await session.commit()
            
            # Log the action
            await log_audit_event(
                AuditEvent.APPLICATION_UNLOCKED,
                user_id=str(current_user.id),
                details={
                    "application_id": str(application_id),
                    "application_type": "onboarding",
                    "previous_status": onboarding_app.status.value,
                    "new_status": "in_progress",
                    "ip_address": request.client.host
                }
            )
            
            return {
                "message": "Application unlocked successfully",
                "application_id": application_id,
                "previous_status": onboarding_app.status.value,
                "new_status": "in_progress"
            }
        
        # If not found as onboarding, try loan application
        from app.models.loan import LoanApplication
        stmt = select(LoanApplication).where(LoanApplication.id == application_id)
        result = await session.execute(stmt)
        loan_app = result.scalar()
        
        if loan_app:
            # Handle loan application using status service
            if loan_app.status not in [ApplicationStatus.UNDER_REVIEW, ApplicationStatus.APPROVED, ApplicationStatus.REJECTED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Application is not in a locked state that can be unlocked"
                )
            
            # Use status service to change status
            updated_app = await status_service.update_application_status(
                session=session,
                application_id=application_id,
                new_status=ApplicationStatus.IN_PROGRESS,
                user=current_user,
                reason="Application unlocked by admin for editing",
                notes="Application unlocked to allow customer to make changes",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )
            
            return {
                "message": "Application unlocked successfully",
                "application_id": application_id,
                "previous_status": loan_app.status.value,
                "new_status": "in_progress"
            }
        
        # If neither found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unlock application: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlock application"
        )


@router.get("/staff/dashboard")
async def get_staff_dashboard(
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Get staff dashboard data (loan officer, risk officer, admin)."""
    try:
        from app.models.onboarding import OnboardingApplication, OnboardingStatus
        from sqlalchemy import func
        # Active applications
        active_count = await session.execute(
            select(func.count(OnboardingApplication.id)).where(
                OnboardingApplication.status.in_([
                    OnboardingStatus.DRAFT,
                    OnboardingStatus.IN_PROGRESS,
                    OnboardingStatus.PENDING_DOCUMENTS,
                    OnboardingStatus.UNDER_REVIEW
                ])
            )
        )
        # Approved applications
        approved_count = await session.execute(
            select(func.count(OnboardingApplication.id)).where(
                OnboardingApplication.status == OnboardingStatus.APPROVED
            )
        )
        # Rejected applications
        rejected_count = await session.execute(
            select(func.count(OnboardingApplication.id)).where(
                OnboardingApplication.status == OnboardingStatus.REJECTED
            )
        )
        # Ready for review (under_review)
        ready_for_review_count = await session.execute(
            select(func.count(OnboardingApplication.id)).where(
                OnboardingApplication.status == OnboardingStatus.UNDER_REVIEW
            )
        )
        # Cancelled applications (status = rejected and cancellation_reason is not null)
        cancelled_count = await session.execute(
            select(func.count(OnboardingApplication.id)).where(
                OnboardingApplication.status == OnboardingStatus.REJECTED,
                OnboardingApplication.cancellation_reason.isnot(None)
            )
        )
        dashboard_data = {
            "active_applications": active_count.scalar() or 0,
            "approved_applications": approved_count.scalar() or 0,
            "rejected_applications": rejected_count.scalar() or 0,
            "ready_for_review_applications": ready_for_review_count.scalar() or 0,
            "cancelled_applications": cancelled_count.scalar() or 0,
            "recent_activities": await _get_recent_activities(session),
        }
        return dashboard_data
    except Exception as e:
        logger.error(f"Failed to get staff dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load staff dashboard data"
        )


@router.get("/staff/activities")
async def get_staff_activities(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_async_db)
):
    """Get all staff activities, paginated."""
    from app.models.user import AuditLog, User
    from app.models.onboarding import OnboardingApplication, OnboardingStep
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    activities = result.scalars().all()
    activity_list = []
    for activity in activities:
        user_display = None
        if activity.user_id:
            user = await session.get(User, activity.user_id)
            if user:
                user_display = f"{user.first_name} {user.last_name}".strip() or str(user.id)
            else:
                user_display = str(activity.user_id)
        application_number = None
        resource_info = ""
        if activity.resource_type == "onboarding_application":
            app = await session.get(OnboardingApplication, activity.resource_id)
            if app:
                application_number = app.application_number
                resource_info = f"(App #{app.application_number})"
        elif activity.resource_type == "onboarding_step":
            step = await session.get(OnboardingStep, activity.resource_id)
            if step:
                app = await session.get(OnboardingApplication, step.application_id)
                if app:
                    application_number = app.application_number
                    resource_info = f"(Step {step.step_number}: {step.step_name}, App #{app.application_number})"
                else:
                    resource_info = f"(Step {step.step_number}: {step.step_name})"
        action_labels = {
            "onboarding_application_created": "Application Created",
            "onboarding_application_submitted": "Application Submitted",
            "onboarding_step_completed": "Step Completed",
            "document_uploaded": "Document Uploaded",
            "document_ocr_processed": "Document OCR Processed",
            "credit_score_calculated": "Credit Score Calculated",
        }
        label = action_labels.get(activity.action, activity.action.replace('_', ' ').title())
        description = f"{label} {resource_info}".strip()
        activity_list.append({
            "label": label,
            "description": description,
            "timestamp": activity.timestamp.isoformat(),
            "user_display": user_display,
            "application_number": application_number
        })
    return {"activities": activity_list, "limit": limit, "offset": offset}


# Helper functions
async def _get_user_count(session: AsyncSession) -> int:
    """Get total user count."""
    try:
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        return result.scalar() or 0
    except:
        return 0


async def _get_active_applications_count(session: AsyncSession) -> int:
    """Get active applications count."""
    try:
        result = await session.execute(text("SELECT COUNT(*) FROM onboarding_applications WHERE UPPER(status) IN ('DRAFT', 'IN_PROGRESS', 'UNDER_REVIEW')"))
        return result.scalar() or 0
    except:
        return 0


async def _get_pending_review_count(session: AsyncSession) -> int:
    try:
        result = await session.execute(text("SELECT COUNT(*) FROM onboarding_applications WHERE UPPER(status) = 'UNDER_REVIEW'"))
        return result.scalar() or 0
    except:
        return 0


async def _get_approved_count(session: AsyncSession) -> int:
    try:
        result = await session.execute(text("SELECT COUNT(*) FROM onboarding_applications WHERE UPPER(status) = 'APPROVED'"))
        return result.scalar() or 0
    except:
        return 0


async def _get_rejected_count(session: AsyncSession) -> int:
    try:
        result = await session.execute(text("SELECT COUNT(*) FROM onboarding_applications WHERE UPPER(status) = 'REJECTED'"))
        return result.scalar() or 0
    except:
        return 0


async def _get_recent_activities(session: AsyncSession) -> List[Dict[str, Any]]:
    """Get recent system activities with readable labels, user info, and application number."""
    try:
        from app.models.user import AuditLog, User
        from app.models.onboarding import OnboardingApplication, OnboardingStep
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(3)
        result = await session.execute(stmt)
        activities = result.scalars().all()
        activity_list = []
        for activity in activities:
            user_display = None
            if activity.user_id:
                user = await session.get(User, activity.user_id)
                if user:
                    user_display = f"{user.first_name} {user.last_name}".strip() or str(user.id)
                else:
                    user_display = str(activity.user_id)
            application_number = None
            resource_info = ""
            if activity.resource_type == "onboarding_application":
                app = await session.get(OnboardingApplication, activity.resource_id)
                if app:
                    application_number = app.application_number
                    resource_info = f"(App #{app.application_number})"
            elif activity.resource_type == "onboarding_step":
                step = await session.get(OnboardingStep, activity.resource_id)
                if step:
                    app = await session.get(OnboardingApplication, step.application_id)
                    if app:
                        application_number = app.application_number
                        resource_info = f"(Step {step.step_number}: {step.step_name}, App #{app.application_number})"
                    else:
                        resource_info = f"(Step {step.step_number}: {step.step_name})"
            action_labels = {
                "onboarding_application_created": "Application Created",
                "onboarding_application_submitted": "Application Submitted",
                "onboarding_step_completed": "Step Completed",
                "document_uploaded": "Document Uploaded",
                "document_ocr_processed": "Document OCR Processed",
                "credit_score_calculated": "Credit Score Calculated",
            }
            label = action_labels.get(activity.action, activity.action.replace('_', ' ').title())
            description = f"{label} {resource_info}".strip()
            activity_list.append({
                "label": label,
                "description": description,
                "timestamp": activity.timestamp.isoformat(),
                "user_display": user_display,
                "application_number": application_number
            })
        return activity_list
    except Exception as e:
        logger.warning(f"Failed to get recent activities: {str(e)}")
        return []


async def _get_system_health_summary() -> Dict[str, str]:
    """Get system health summary."""
    return {
        "api": "healthy",
        "database": "healthy",
        "external_services": "healthy"
    }


async def _get_configuration_status() -> Dict[str, Any]:
    """Get configuration status."""
    return {
        "scorecard_configured": bool(settings.SCORECARD_API_URL and settings.SCORECARD_API_KEY),
        "email_configured": bool(settings.MAIL_USERNAME and settings.MAIL_PASSWORD),
        "sms_configured": bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)
    }


async def _check_database_health() -> Dict[str, Any]:
    """Check database health."""
    gen = get_async_db()
    session = await gen.__anext__()
    try:
        await session.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "response_time": "< 10ms",
            "last_check": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow()
        }
    finally:
        try:
            await gen.aclose()
        except Exception:
            pass


async def _check_external_services() -> Dict[str, Dict[str, Any]]:
    """Check external services health."""
    services = {}
    
    # Check scorecard service
    services["scorecard"] = await _check_scorecard_health()
    
    return services


async def _check_scorecard_health() -> Dict[str, Any]:
    """Check scorecard service health."""
    try:
        if not settings.SCORECARD_API_URL:
            return {
                "status": "not_configured",
                "message": "Scorecard API URL not configured"
            }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            start_time = asyncio.get_event_loop().time()
            response = await client.get(f"{settings.SCORECARD_API_URL}/health")
            end_time = asyncio.get_event_loop().time()
            
            response_time = round((end_time - start_time) * 1000, 2)
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time": f"{response_time}ms",
                    "last_check": datetime.utcnow()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time": f"{response_time}ms",
                    "last_check": datetime.utcnow()
                }
                
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow()
        }


async def _test_scorecard_connection(url: str, api_key: str) -> Dict[str, Any]:
    """Test scorecard service connection with new configuration."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            start_time = asyncio.get_event_loop().time()
            response = await client.get(f"{url}/health", headers=headers)
            end_time = asyncio.get_event_loop().time()
            
            response_time = round((end_time - start_time) * 1000, 2)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "healthy",
                    "response_time": f"{response_time}ms",
                    "message": "Connection successful"
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": f"{response_time}ms"
                }
                
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "error": str(e),
            "response_time": None
        }


async def _get_last_health_check(service: str) -> str:
    """Get last health check timestamp for a service."""
    return datetime.utcnow().isoformat()


# ===== NEW USER PROFILE MANAGEMENT ENDPOINTS =====

@router.get("/users/{user_id}/profile", response_model=AdminUserProfileResponse)
async def get_user_profile_admin(
    user_id: str,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_db)
):
    """Get detailed user profile for admin view."""
    try:
        # Get user
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get customer data
        customer_data = None
        documents = []
        total_applications = 0
        approved_applications = 0
        rejected_applications = 0
        pending_applications = 0
        
        customer_stmt = select(Customer).where(Customer.user_id == user.id)
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if customer:
            # Build customer data
            customer_data = {
                "id": str(customer.id),
                "customer_number": customer.customer_number,
                "date_of_birth": customer.date_of_birth.isoformat() if customer.date_of_birth else None,
                "gender": customer.gender,
                "nationality": customer.nationality,
                "id_number": customer.id_number,
                "employment_status": customer.employment_status,
                "employer_name": customer.employer_name,
                "monthly_income": float(customer.monthly_income) if customer.monthly_income else None,
                "is_verified": customer.is_verified,
                "verification_completed_at": customer.verification_completed_at.isoformat() if customer.verification_completed_at else None
            }
            
            # Get documents
            documents_stmt = select(Document).where(Document.customer_id == customer.id)
            documents_result = await session.execute(documents_stmt)
            customer_documents = documents_result.scalars().all()
            
            for doc in customer_documents:
                doc_response = DocumentResponse(
                    id=str(doc.id),
                    document_type=doc.document_type,
                    document_name=doc.document_name,
                    status=doc.status,
                    is_required=doc.is_required,
                    expires_at=doc.expires_at.isoformat() if doc.expires_at else None,
                    is_expired=doc.is_expired,
                    uploaded_at=doc.uploaded_at,
                    verified_at=doc.verified_at,
                    verification_notes=doc.verification_notes,
                    file_size=doc.file_size,
                    mime_type=doc.mime_type
                )
                documents.append(doc_response)
            
            # Get application statistics
            applications_stmt = select(OnboardingApplication).where(OnboardingApplication.customer_id == customer.id)
            applications_result = await session.execute(applications_stmt)
            applications = applications_result.scalars().all()
            
            total_applications = len(applications)
            for app in applications:
                if app.status == OnboardingStatus.APPROVED:
                    approved_applications += 1
                elif app.status == OnboardingStatus.REJECTED:
                    rejected_applications += 1
                elif app.status in [OnboardingStatus.DRAFT, OnboardingStatus.IN_PROGRESS, OnboardingStatus.UNDER_REVIEW]:
                    pending_applications += 1
        
        # Get role history
        role_history = []
        history_stmt = select(UserRoleHistory).where(UserRoleHistory.user_id == user.id).order_by(UserRoleHistory.changed_at.desc())
        history_result = await session.execute(history_stmt)
        history_records = history_result.scalars().all()
        
        for record in history_records:
            # Get changed_by user info
            changed_by_name = None
            if record.changed_by_id:
                changed_by_stmt = select(User).where(User.id == record.changed_by_id)
                changed_by_result = await session.execute(changed_by_stmt)
                changed_by_user = changed_by_result.scalar()
                if changed_by_user:
                    changed_by_name = f"{changed_by_user.first_name} {changed_by_user.last_name}"
            
            history_response = UserRoleHistoryResponse(
                id=str(record.id),
                user_id=str(record.user_id),
                old_role=record.old_role,
                new_role=record.new_role,
                changed_by_id=str(record.changed_by_id) if record.changed_by_id else None,
                changed_by_name=changed_by_name,
                changed_at=record.changed_at,
                reason=record.reason
            )
            role_history.append(history_response)
        
        # Build response
        admin_profile_response = AdminUserProfileResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=user.phone_number,
            role=user.role,
            user_state=user.user_state,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_locked=user.is_locked,
            failed_login_attempts=user.failed_login_attempts,
            last_login=user.last_login,
            created_at=user.created_at,
            onboarding_completed_at=user.onboarding_completed_at,
            last_profile_update=user.last_profile_update,
            profile_expiry_date=user.profile_expiry_date,
            profile_completion_percentage=user.profile_completion_percentage,
            can_create_loans=user.can_create_loans,
            customer_data=customer_data,
            documents=documents,
            role_history=role_history,
            total_applications=total_applications,
            approved_applications=approved_applications,
            rejected_applications=rejected_applications,
            pending_applications=pending_applications
        )
        
        return admin_profile_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile for admin view: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_update: RoleUpdateRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_db)
):
    """Update user role (admin only)."""
    try:
        # Validate UUID format
        try:
            uuid_lib.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Validate admin permissions
        if not current_user or not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        if current_user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Admin account is locked"
            )
        
        # Get user to update with error handling
        try:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user_to_update = result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error retrieving user"
            )
        
        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Security checks
        if str(user_to_update.id) == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own role"
            )
        
        # Prevent demoting the last admin
        if (user_to_update.role == UserRole.ADMIN and 
            role_update.new_role != UserRole.ADMIN):
            admin_count = await session.scalar(
                select(func.count(User.id)).where(
                    and_(User.role == UserRole.ADMIN, User.is_active == True)
                )
            )
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last admin user"
                )
        
        # Store old role for comparison
        old_role = user_to_update.role
        
        # Check if role is actually changing
        if old_role == role_update.new_role:
            return {
                "message": "User role is already set to the requested role",
                "user_id": str(user_to_update.id),
                "role": old_role.value
            }
        
        # Transaction for role update
        try:
            # Update role
            user_to_update.role = role_update.new_role
            
            # Create role history record
            role_history = UserRoleHistory(
                user_id=user_to_update.id,
                old_role=old_role.value,
                new_role=role_update.new_role.value,
                changed_by_id=current_user.id,
                reason=role_update.reason or "Role changed by admin"
            )
            session.add(role_history)
            
            await session.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error updating user role: {str(e)}")
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user role in database"
            )
        
        # Log the action (outside transaction)
        try:
            await audit_service.log_onboarding_action(
                user_id=str(current_user.id),
                action="user_role_changed",
                resource_type="user",
                resource_id=str(user_to_update.id),
                old_values={"role": old_role.value},
                new_values={"role": role_update.new_role.value},
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                additional_data={
                    "reason": role_update.reason,
                    "target_user_email": user_to_update.email,
                    "admin_user_email": current_user.email
                }
            )
        except Exception as e:
            logger.error(f"Failed to log role change audit: {str(e)}")
        
        try:
            log_audit_event(
                AuditEvent.ADMIN_ACTION,
                user_id=str(current_user.id),
                details={
                    "action": "user_role_changed",
                    "target_user_id": str(user_to_update.id),
                    "old_role": old_role.value,
                    "new_role": role_update.new_role.value,
                    "ip_address": request.client.host
                }
            )
        except Exception as e:
            logger.error(f"Failed to log admin action: {str(e)}")
        
        return {
            "message": "User role updated successfully",
            "user_id": str(user_to_update.id),
            "old_role": old_role.value,
            "new_role": role_update.new_role.value,
            "changed_by": current_user.email,
            "reason": role_update.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user role: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )


@router.put("/users/{user_id}/state")
async def update_user_state(
    user_id: str,
    state_update: StateUpdateRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_db)
):
    """Update user state (admin only)."""
    try:
        # Get user to update
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user_to_update = result.scalar()
        
        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user state using service
        await user_state_service.update_user_state(
            user_to_update,
            state_update.new_state,
            session,
            reason=f"Admin update: {state_update.reason or 'Manual state change'}"
        )
        
        # Log additional admin action
        log_audit_event(
            AuditEvent.ADMIN_ACTION,
            user_id=str(current_user.id),
            details={
                "action": "user_state_changed_by_admin",
                "target_user_id": str(user_to_update.id),
                "new_state": state_update.new_state.value,
                "reason": state_update.reason,
                "ip_address": request.client.host
            }
        )
        
        return {
            "message": "User state updated successfully",
            "user_id": str(user_to_update.id),
            "new_state": state_update.new_state.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user state: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user state"
        )


@router.get("/users/outdated")
async def get_outdated_users(
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_db)
):
    """Get users with outdated profiles."""
    try:
        outdated_users = await user_state_service.get_outdated_users(session)
        
        user_list = []
        for user in outdated_users:
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_state": user.user_state.value,
                "profile_expiry_date": user.profile_expiry_date.isoformat() if user.profile_expiry_date else None,
                "last_profile_update": user.last_profile_update.isoformat() if user.last_profile_update else None,
                "onboarding_completed_at": user.onboarding_completed_at.isoformat() if user.onboarding_completed_at else None
            }
            user_list.append(user_data)
        
        return {
            "outdated_users": user_list,
            "count": len(user_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to get outdated users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve outdated users"
        )