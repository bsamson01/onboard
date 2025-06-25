from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import logging

from app.database import get_async_session
from app.models.user import User
from app.models.mfi_config import MFIInstitution, ExternalServiceConfig, ServiceType, ServiceStatus
from app.core.auth import require_admin
from app.services.mfi_service_manager import mfi_service_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """Get admin dashboard overview."""
    try:
        # Get institution count
        institutions_stmt = select(MFIInstitution).where(MFIInstitution.is_active == True)
        institutions_result = await session.execute(institutions_stmt)
        active_institutions = len(institutions_result.scalars().all())
        
        # Get service configurations
        services_stmt = select(ExternalServiceConfig)
        services_result = await session.execute(services_stmt)
        all_services = services_result.scalars().all()
        
        active_services = len([s for s in all_services if s.status == ServiceStatus.ACTIVE])
        error_services = len([s for s in all_services if s.status == ServiceStatus.ERROR])
        
        # Service breakdown by type
        service_breakdown = {}
        for service in all_services:
            service_type = service.service_type
            if service_type not in service_breakdown:
                service_breakdown[service_type] = {"total": 0, "active": 0, "error": 0}
            
            service_breakdown[service_type]["total"] += 1
            if service.status == ServiceStatus.ACTIVE:
                service_breakdown[service_type]["active"] += 1
            elif service.status == ServiceStatus.ERROR:
                service_breakdown[service_type]["error"] += 1
        
        return {
            "summary": {
                "active_institutions": active_institutions,
                "total_services": len(all_services),
                "active_services": active_services,
                "error_services": error_services
            },
            "service_breakdown": service_breakdown
        }
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard")

@router.get("/institutions")
async def list_institutions(
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """List all MFI institutions."""
    stmt = select(MFIInstitution)
    result = await session.execute(stmt)
    institutions = result.scalars().all()
    
    return [
        {
            "id": str(institution.id),
            "code": institution.code,
            "name": institution.name,
            "display_name": institution.display_name,
            "is_active": institution.is_active,
            "country": institution.country,
            "business_model": institution.business_model,
            "minimum_credit_score": institution.minimum_credit_score,
            "created_at": institution.created_at.isoformat()
        }
        for institution in institutions
    ]

@router.post("/institutions")
async def create_institution(
    institution_data: Dict[str, Any],
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new MFI institution."""
    try:
        new_institution = MFIInstitution(
            code=institution_data["code"],
            name=institution_data["name"],
            display_name=institution_data["display_name"],
            description=institution_data.get("description"),
            contact_email=institution_data.get("contact_email"),
            contact_phone=institution_data.get("contact_phone"),
            country=institution_data.get("country"),
            business_model=institution_data.get("business_model"),
            minimum_credit_score=institution_data.get("minimum_credit_score", 600),
            created_by_id=current_user.id
        )
        
        session.add(new_institution)
        await session.commit()
        
        return {"id": str(new_institution.id), "message": "Institution created successfully"}
    except Exception as e:
        logger.error(f"Institution creation error: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to create institution")

@router.get("/institutions/{institution_id}/services")
async def list_institution_services(
    institution_id: str,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """List services for an institution."""
    stmt = select(ExternalServiceConfig).where(
        ExternalServiceConfig.institution_id == institution_id
    )
    result = await session.execute(stmt)
    services = result.scalars().all()
    
    return [
        {
            "id": str(service.id),
            "service_type": service.service_type,
            "service_name": service.service_name,
            "service_provider": service.service_provider,
            "status": service.status,
            "is_primary": service.is_primary,
            "success_rate": service.success_rate,
            "total_calls": service.total_calls,
            "last_health_check": service.last_health_check.isoformat() if service.last_health_check else None,
            "is_healthy": service.is_healthy
        }
        for service in services
    ]

@router.post("/institutions/{institution_id}/services")
async def create_service_config(
    institution_id: str,
    service_data: Dict[str, Any],
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new service configuration."""
    try:
        # Encrypt sensitive data
        encrypted_api_key = None
        if service_data.get("api_key"):
            encrypted_api_key = mfi_service_manager.encrypt_credential(service_data["api_key"])
        
        new_service = ExternalServiceConfig(
            institution_id=institution_id,
            service_type=service_data["service_type"],
            service_name=service_data["service_name"],
            service_provider=service_data.get("service_provider"),
            api_url=service_data["api_url"],
            api_key=encrypted_api_key,
            timeout_seconds=service_data.get("timeout_seconds", 30),
            is_primary=service_data.get("is_primary", False),
            config_parameters=service_data.get("config_parameters"),
            created_by_id=current_user.id
        )
        
        session.add(new_service)
        await session.commit()
        
        return {"id": str(new_service.id), "message": "Service configuration created successfully"}
    except Exception as e:
        logger.error(f"Service creation error: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to create service configuration")

@router.post("/services/{service_id}/health-check")
async def run_service_health_check(
    service_id: str,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """Run health check on a service."""
    try:
        stmt = select(ExternalServiceConfig).where(ExternalServiceConfig.id == service_id)
        result = await session.execute(stmt)
        service = result.scalar()
        
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        is_healthy = await mfi_service_manager.health_check_service(service, session)
        
        return {
            "service_id": service_id,
            "is_healthy": is_healthy,
            "status": service.status,
            "last_check": service.last_health_check.isoformat() if service.last_health_check else None,
            "error_count": service.error_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/services/{service_id}/metrics")
async def get_service_metrics(
    service_id: str,
    days: int = 7,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """Get metrics for a specific service."""
    try:
        stmt = (
            select(ExternalServiceConfig)
            .join(MFIInstitution)
            .where(ExternalServiceConfig.id == service_id)
        )
        result = await session.execute(stmt)
        service = result.scalar()
        
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        metrics = await mfi_service_manager.get_service_metrics(
            service.institution.code,
            ServiceType(service.service_type),
            days,
            session
        )
        
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """Get overall system health status."""
    try:
        # Get all active services
        stmt = select(ExternalServiceConfig).where(
            ExternalServiceConfig.status == ServiceStatus.ACTIVE
        )
        result = await session.execute(stmt)
        active_services = result.scalars().all()
        
        health_status = {
            "overall_status": "healthy",
            "services": [],
            "summary": {
                "total_services": len(active_services),
                "healthy_services": 0,
                "unhealthy_services": 0
            }
        }
        
        for service in active_services:
            is_healthy = service.is_healthy
            
            service_health = {
                "service_id": str(service.id),
                "service_name": service.service_name,
                "service_type": service.service_type,
                "institution": service.institution.name,
                "is_healthy": is_healthy,
                "success_rate": service.success_rate,
                "last_check": service.last_health_check.isoformat() if service.last_health_check else None
            }
            
            health_status["services"].append(service_health)
            
            if is_healthy:
                health_status["summary"]["healthy_services"] += 1
            else:
                health_status["summary"]["unhealthy_services"] += 1
        
        # Determine overall status
        if health_status["summary"]["unhealthy_services"] > 0:
            unhealthy_ratio = health_status["summary"]["unhealthy_services"] / len(active_services)
            if unhealthy_ratio > 0.5:
                health_status["overall_status"] = "critical"
            else:
                health_status["overall_status"] = "degraded"
        
        return health_status
    except Exception as e:
        logger.error(f"System health check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check system health")