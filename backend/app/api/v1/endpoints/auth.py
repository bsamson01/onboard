from datetime import timedelta, datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_async_db
from app.core.auth import authenticate_user, create_access_token, get_current_user, create_user, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import Token, UserCreate, UserResponse, LoginRequest, PasswordChange
from app.config import settings
from app.core.logging import log_security_event, log_audit_event, SecurityEvent, AuditEvent

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(db, email=user_data.email)
        if existing_user:
            log_security_event(
                SecurityEvent.SUSPICIOUS_ACTIVITY,
                ip_address=request.client.host,
                details={"reason": "attempted_duplicate_registration", "email": user_data.email}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = await create_user(db, user_data)
        
        # Log successful registration
        log_audit_event(
            AuditEvent.USER_CREATED,
            user_id=str(user.id),
            details={
                "email": user.email,
                "role": user.role.value,
                "ip_address": request.client.host
            }
        )
        
        log_security_event(
            SecurityEvent.LOGIN_SUCCESS,
            ip_address=request.client.host,
            user_id=str(user.id),
            details={"event": "user_registration"}
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            ip_address=request.client.host,
            details={"error": str(e), "event": "registration_failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Login endpoint that returns JWT tokens (OAuth2 form-based)."""
    try:
        # Authenticate user
        user = await authenticate_user(db, form_data.username, form_data.password)
        
        if not user:
            log_security_event(
                SecurityEvent.LOGIN_FAILED,
                ip_address=request.client.host,
                details={"username": form_data.username, "reason": "invalid_credentials"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            log_security_event(
                SecurityEvent.LOGIN_FAILED,
                ip_address=request.client.host,
                user_id=str(user.id),
                details={"reason": "account_inactive"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        if user.is_locked:
            log_security_event(
                SecurityEvent.LOGIN_LOCKED,
                ip_address=request.client.host,
                user_id=str(user.id),
                details={"reason": "account_locked"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked. Please contact support."
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": str(user.id)},
            expires_delta=access_token_expires
        )
        
        # Update last login
        await update_user_last_login(db, user.id, request.client.host)
        
        # Log successful login
        log_security_event(
            SecurityEvent.LOGIN_SUCCESS,
            ip_address=request.client.host,
            user_id=str(user.id),
            details={"login_method": "password"}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": UserResponse.model_validate(user).model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            ip_address=request.client.host,
            details={"error": str(e), "event": "login_failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/login-json", response_model=Token)
async def login_json(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Login endpoint that accepts JSON data with email and password."""
    try:
        # Authenticate user using email
        user = await authenticate_user(db, login_data.email, login_data.password)
        
        if not user:
            log_security_event(
                SecurityEvent.LOGIN_FAILED,
                ip_address=request.client.host,
                details={"email": login_data.email, "reason": "invalid_credentials"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            log_security_event(
                SecurityEvent.LOGIN_FAILED,
                ip_address=request.client.host,
                user_id=str(user.id),
                details={"reason": "account_inactive"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        if user.is_locked:
            log_security_event(
                SecurityEvent.LOGIN_LOCKED,
                ip_address=request.client.host,
                user_id=str(user.id),
                details={"reason": "account_locked"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked. Please contact support."
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": str(user.id)},
            expires_delta=access_token_expires
        )
        
        # Update last login
        await update_user_last_login(db, user.id, request.client.host)
        
        # Log successful login
        log_security_event(
            SecurityEvent.LOGIN_SUCCESS,
            ip_address=request.client.host,
            user_id=str(user.id),
            details={"login_method": "password_json"}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": UserResponse.model_validate(user).model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            ip_address=request.client.host,
            details={"error": str(e), "event": "login_failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Refresh JWT token."""
    try:
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": current_user.email, "user_id": str(current_user.id)},
            expires_delta=access_token_expires
        )
        
        log_audit_event(
            "token_refreshed",
            user_id=str(current_user.id),
            details={"ip_address": request.client.host}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": current_user
        }
        
    except Exception as e:
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            ip_address=request.client.host,
            user_id=str(current_user.id),
            details={"error": str(e), "event": "token_refresh_failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Logout endpoint."""
    try:
        # TODO: Implement token blacklisting with Redis
        # For now, we'll just log the logout event
        
        log_audit_event(
            "user_logout",
            user_id=str(current_user.id),
            details={"ip_address": request.client.host}
        )
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            ip_address=request.client.host,
            user_id=str(current_user.id),
            details={"error": str(e), "event": "logout_failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Change user password."""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            log_security_event(
                SecurityEvent.SUSPICIOUS_ACTIVITY,
                ip_address=request.client.host,
                user_id=str(current_user.id),
                details={"reason": "invalid_current_password", "event": "password_change_attempted"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        hashed_password = get_password_hash(password_data.new_password)
        await update_user_password(db, current_user.id, hashed_password)
        
        # Log password change
        log_security_event(
            SecurityEvent.PASSWORD_CHANGED,
            ip_address=request.client.host,
            user_id=str(current_user.id)
        )
        
        log_audit_event(
            "password_changed",
            user_id=str(current_user.id),
            details={"ip_address": request.client.host}
        )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            ip_address=request.client.host,
            user_id=str(current_user.id),
            details={"error": str(e), "event": "password_change_failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user information."""
    return current_user


@router.get("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Verify if the current token is valid."""
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role.value
    }


# Helper functions (these would typically be in a separate service module)
async def get_user_by_email(db: AsyncSession, email: str):
    """Get user by email."""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar()


async def update_user_last_login(db: AsyncSession, user_id: str, ip_address: str):
    """Update user's last login timestamp."""
    # Get the user and update directly
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar()
    
    if user:
        user.last_login = datetime.now()
        # The changes will be committed by the dependency injection


async def update_user_password(db: AsyncSession, user_id: str, hashed_password: str):
    """Update user's password."""
    # Get the user and update directly
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar()
    
    if user:
        user.hashed_password = hashed_password
        user.password_changed_at = datetime.now()
        # The changes will be committed by the dependency injection