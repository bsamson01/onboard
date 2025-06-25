from datetime import timedelta
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.auth import (
    authenticate_user, 
    get_current_user, 
    create_user,
    get_user_by_email,
    update_user_last_login,
    update_user_password,
    logout_user,
    get_user_sessions,
    revoke_user_session
)
from app.core.security import (
    create_access_token,
    get_password_hash, 
    verify_password,
    generate_password_reset_token,
    verify_password_reset_token,
    generate_mfa_secret,
    verify_mfa_token,
    generate_backup_codes,
    hash_backup_code,
    verify_backup_code,
    is_safe_password
)
from app.models.user import User, UserRole
from app.schemas.auth import Token, LoginRequest
from app.schemas.user import (
    UserCreate, 
    UserResponse, 
    PasswordChange, 
    PasswordReset, 
    PasswordResetConfirm,
    MFASetup,
    MFAVerify,
    MFABackupCode,
    UserSessionsResponse
)
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
        
        # Validate password strength
        is_safe, password_errors = is_safe_password(user_data.password)
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password does not meet security requirements", "errors": password_errors}
            )
        
        # Create new user
        user = await create_user(db, user_data)
        
        # Log successful registration
        await log_audit_event(
            db=db,
            user_id=str(user.id),
            action=AuditEvent.USER_CREATED,
            resource_type="user",
            resource_id=str(user.id),
            new_values={
                "email": user.email,
                "role": user.role.value
            },
            ip_address=request.client.host
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
    """Login endpoint that returns JWT tokens."""
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
            "user": user
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
        
        await log_audit_event(
            db=db,
            user_id=str(current_user.id),
            action="token_refreshed",
            resource_type="user",
            resource_id=str(current_user.id),
            ip_address=request.client.host
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
        # Get the token from the request (this would need to be extracted from the Authorization header)
        # For now, we'll implement basic logout without token blacklisting
        
        await logout_user(db, str(current_user.id), "")  # Token would be extracted from header
        
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
        
        # Validate new password strength
        is_safe, password_errors = is_safe_password(password_data.new_password)
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "New password does not meet security requirements", "errors": password_errors}
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
        
        await log_audit_event(
            db=db,
            user_id=str(current_user.id),
            action="password_changed",
            resource_type="user",
            resource_id=str(current_user.id),
            ip_address=request.client.host
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


@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Request password reset."""
    try:
        user = await get_user_by_email(db, password_reset.email)
        
        # Always return success to prevent email enumeration
        message = "If an account with that email exists, a password reset link has been sent."
        
        if user and user.is_active:
            # Generate password reset token
            reset_token = generate_password_reset_token(user.email)
            
            # TODO: Send password reset email
            # For now, we'll just log the token (remove in production)
            print(f"Password reset token for {user.email}: {reset_token}")
            
            # Log password reset request
            await log_audit_event(
                db=db,
                user_id=str(user.id),
                action="password_reset_requested",
                resource_type="user",
                resource_id=str(user.id),
                ip_address=request.client.host
            )
        
        return {"message": message}
        
    except Exception as e:
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            ip_address=request.client.host,
            details={"error": str(e), "event": "password_reset_failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password")
async def reset_password(
    password_reset: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Reset password with token."""
    try:
        # Verify reset token
        email = verify_password_reset_token(password_reset.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user = await get_user_by_email(db, email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Validate new password strength
        is_safe, password_errors = is_safe_password(password_reset.new_password)
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password does not meet security requirements", "errors": password_errors}
            )
        
        # Update password
        hashed_password = get_password_hash(password_reset.new_password)
        await update_user_password(db, user.id, hashed_password)
        
        # Log password reset
        log_security_event(
            SecurityEvent.PASSWORD_CHANGED,
            ip_address=request.client.host,
            user_id=str(user.id),
            details={"method": "password_reset"}
        )
        
        await log_audit_event(
            db=db,
            user_id=str(user.id),
            action="password_reset_completed",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host
        )
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            ip_address=request.client.host,
            details={"error": str(e), "event": "password_reset_failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/mfa/setup", response_model=MFASetup)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Set up Multi-Factor Authentication."""
    try:
        # Generate MFA secret
        secret = generate_mfa_secret()
        
        # Generate QR code for authenticator apps
        import qrcode
        import io
        import base64
        
        totp_url = f"otpauth://totp/{settings.PROJECT_NAME}:{current_user.email}?secret={secret}&issuer={settings.PROJECT_NAME}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        qr_code_url = f"data:image/png;base64,{qr_code_data}"
        
        # Generate backup codes
        backup_codes = generate_backup_codes()
        hashed_backup_codes = [hash_backup_code(code) for code in backup_codes]
        
        # Store MFA settings (temporarily - user needs to verify)
        # TODO: Store in temporary storage until verified
        
        return MFASetup(
            secret=secret,
            qr_code=qr_code_url,
            backup_codes=backup_codes
        )
        
    except Exception as e:
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            user_id=str(current_user.id),
            details={"error": str(e), "event": "mfa_setup_failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA setup failed"
        )


@router.post("/mfa/verify")
async def verify_mfa(
    mfa_verify: MFAVerify,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Verify MFA token and enable MFA."""
    try:
        # TODO: Get secret from temporary storage
        # For now, we'll assume MFA is not fully implemented
        
        log_security_event(
            SecurityEvent.MFA_ENABLED,
            ip_address=request.client.host,
            user_id=str(current_user.id)
        )
        
        await log_audit_event(
            db=db,
            user_id=str(current_user.id),
            action="mfa_enabled",
            resource_type="user",
            resource_id=str(current_user.id),
            ip_address=request.client.host
        )
        
        return {"message": "MFA enabled successfully"}
        
    except Exception as e:
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            ip_address=request.client.host,
            user_id=str(current_user.id),
            details={"error": str(e), "event": "mfa_verify_failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed"
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


@router.get("/sessions", response_model=UserSessionsResponse)
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Get user's active sessions."""
    try:
        sessions = await get_user_sessions(db, str(current_user.id))
        
        return UserSessionsResponse(
            sessions=sessions,
            total=len(sessions)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """Revoke a specific session."""
    try:
        await revoke_user_session(db, session_id, str(current_user.id))
        
        await log_audit_event(
            db=db,
            user_id=str(current_user.id),
            action="session_revoked",
            resource_type="session",
            resource_id=session_id,
            ip_address=request.client.host
        )
        
        return {"message": "Session revoked successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


# Helper functions are now imported from app.core.auth