from typing import Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_

from app.database import get_async_db
from app.core.auth import get_current_user, require_admin
from app.models.user import User, UserRole, AuditLog, UserSession
from app.schemas.user import UserResponse, UserListResponse, UserUpdateAdmin
from app.schemas.auth import AuditLogResponse, AuditLogEntry
from app.core.logging import log_audit_event, SecurityEvent, log_security_event

router = APIRouter()


@router.get("/dashboard")
async def admin_dashboard(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Admin dashboard overview with key metrics."""
    
    # Get user statistics
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
    locked_users = await db.scalar(select(func.count(User.id)).where(User.is_locked == True))
    
    # Get role distribution
    role_stats = {}
    for role in UserRole:
        count = await db.scalar(select(func.count(User.id)).where(User.role == role))
        role_stats[role.value] = count
    
    # Get recent user registrations (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
    )
    
    # Get active sessions
    active_sessions = await db.scalar(
        select(func.count(UserSession.id)).where(UserSession.is_active == True)
    )
    
    return {
        "total_users": total_users or 0,
        "active_users": active_users or 0,
        "locked_users": locked_users or 0,
        "role_distribution": role_stats,
        "recent_registrations": recent_users or 0,
        "active_sessions": active_sessions or 0
    }


@router.get("/users", response_model=UserListResponse)
async def list_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_locked: Optional[bool] = Query(None)
):
    """List all users with filtering and pagination."""
    
    # Build query
    query = select(User)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_term),
                User.username.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term)
            )
        )
    
    if role:
        query = query.where(User.role == role)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    if is_locked is not None:
        query = query.where(User.is_locked == is_locked)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    
    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(User.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=str(current_user.id),
        action="admin_user_list_accessed",
        resource_type="admin",
        additional_data={
            "filters": {
                "search": search,
                "role": role.value if role else None,
                "is_active": is_active,
                "is_locked": is_locked
            }
        }
    )
    
    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific user by ID."""
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=str(current_user.id),
        action="admin_user_viewed",
        resource_type="user",
        resource_id=user_id
    )
    
    return UserResponse.from_orm(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdateAdmin,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a user (admin only)."""
    
    # Get existing user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Store old values for audit
    old_values = {
        "role": user.role.value if user.role else None,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_locked": user.is_locked,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number
    }
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    
    if update_data:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
        )
        await db.commit()
        await db.refresh(user)
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=str(current_user.id),
        action="admin_user_updated",
        resource_type="user",
        resource_id=user_id,
        old_values=old_values,
        new_values=update_data
    )
    
    # Log security event if role changed
    if "role" in update_data:
        log_security_event(
            SecurityEvent.ADMIN_ACTION,
            user_id=str(current_user.id),
            details={
                "action": "role_changed",
                "target_user": user_id,
                "old_role": old_values["role"],
                "new_role": update_data["role"].value if update_data["role"] else None
            }
        )
    
    return UserResponse.from_orm(user)


@router.post("/users/{user_id}/lock")
async def lock_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Lock a user account."""
    
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot lock your own account"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(is_locked=True)
    )
    await db.commit()
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=str(current_user.id),
        action="admin_user_locked",
        resource_type="user",
        resource_id=user_id
    )
    
    log_security_event(
        SecurityEvent.ADMIN_ACTION,
        user_id=str(current_user.id),
        details={
            "action": "user_locked",
            "target_user": user_id
        }
    )
    
    return {"message": "User account locked successfully"}


@router.post("/users/{user_id}/unlock")
async def unlock_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Unlock a user account."""
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(is_locked=False, failed_login_attempts=0)
    )
    await db.commit()
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=str(current_user.id),
        action="admin_user_unlocked",
        resource_type="user",
        resource_id=user_id
    )
    
    log_security_event(
        SecurityEvent.ADMIN_ACTION,
        user_id=str(current_user.id),
        details={
            "action": "user_unlocked",
            "target_user": user_id
        }
    )
    
    return {"message": "User account unlocked successfully"}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Deactivate a user account."""
    
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(is_active=False)
    )
    await db.commit()
    
    # Deactivate all user sessions
    await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id)
        .values(is_active=False)
    )
    await db.commit()
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=str(current_user.id),
        action="admin_user_deactivated",
        resource_type="user",
        resource_id=user_id
    )
    
    log_security_event(
        SecurityEvent.ADMIN_ACTION,
        user_id=str(current_user.id),
        details={
            "action": "user_deactivated",
            "target_user": user_id
        }
    )
    
    return {"message": "User account deactivated successfully"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Activate a user account."""
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(is_active=True)
    )
    await db.commit()
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=str(current_user.id),
        action="admin_user_activated",
        resource_type="user",
        resource_id=user_id
    )
    
    log_security_event(
        SecurityEvent.ADMIN_ACTION,
        user_id=str(current_user.id),
        details={
            "action": "user_activated",
            "target_user": user_id
        }
    )
    
    return {"message": "User account activated successfully"}


@router.get("/audit-logs", response_model=AuditLogResponse)
async def get_audit_logs(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365)
):
    """Get audit logs (admin only)."""
    
    from datetime import datetime, timedelta
    
    # Build query
    query = select(AuditLog)
    
    # Filter by date range
    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.where(AuditLog.timestamp >= start_date)
    
    # Apply filters
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    
    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(AuditLog.timestamp.desc())
    
    # Execute query
    result = await db.execute(query)
    audit_logs = result.scalars().all()
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=str(current_user.id),
        action="admin_audit_logs_accessed",
        resource_type="admin",
        additional_data={
            "filters": {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "days": days
            }
        }
    )
    
    return AuditLogResponse(
        logs=[AuditLogEntry.from_orm(log) for log in audit_logs],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0
    )


@router.get("/reports")
async def get_reports(current_user: User = Depends(require_admin)):
    """Get available admin reports."""
    return {
        "available_reports": [
            {
                "id": "user_activity",
                "name": "User Activity Report",
                "description": "Login activity and user engagement metrics"
            },
            {
                "id": "security_events",
                "name": "Security Events Report", 
                "description": "Failed logins, locked accounts, and security incidents"
            },
            {
                "id": "role_distribution",
                "name": "Role Distribution Report",
                "description": "User count by role and permissions"
            }
        ]
    }


@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Get system health status."""
    try:
        # Test database connection
        await db.execute(select(1))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # TODO: Add Redis health check
    # TODO: Add external service health checks
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "components": {
            "database": db_status,
            "redis": "unknown",  # Implement Redis check
            "external_services": "unknown"  # Implement external service checks
        },
        "timestamp": "2024-01-01T00:00:00Z"  # Current timestamp
    }