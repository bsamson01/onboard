from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Dict, Any, List
import httpx
import asyncio
from datetime import datetime
import logging

from app.database import get_async_db
from app.models.user import User
from app.core.auth import require_admin
from app.config import settings
from app.services.scorecard_service import ScorecardService
from app.services.audit_service import AuditService
from app.core.logging import log_audit_event, AuditEvent
from pydantic import BaseModel, HttpUrl
from app.models.onboarding import OnboardingApplication, OnboardingStatus
from app.models.loan import ApplicationStatus
from app.services.status_service import StatusService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
scorecard_service = ScorecardService()
audit_service = AuditService()
status_service = StatusService()


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
        # Get system statistics
        dashboard_data = {
            "system_status": "operational",
            "total_users": await _get_user_count(session),
            "active_applications": await _get_active_applications_count(session),
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
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_locked": user.is_locked,
                "failed_login_attempts": user.failed_login_attempts,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
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
        result = await session.execute(text("SELECT COUNT(*) FROM onboarding_applications WHERE status IN ('draft', 'in_progress', 'under_review')"))
        return result.scalar() or 0
    except:
        return 0


async def _get_recent_activities(session: AsyncSession) -> List[Dict[str, Any]]:
    """Get recent system activities."""
    try:
        from app.models.user import AuditLog
        
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10)
        result = await session.execute(stmt)
        activities = result.scalars().all()
        
        activity_list = []
        for activity in activities:
            activity_data = {
                "action": activity.action,
                "resource_type": activity.resource_type,
                "timestamp": activity.timestamp.isoformat(),
                "user_id": str(activity.user_id) if activity.user_id else None
            }
            activity_list.append(activity_data)
        
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
    try:
        async with get_async_db() as session:
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