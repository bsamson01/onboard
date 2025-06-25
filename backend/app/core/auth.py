from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from jose import JWTError, jwt
import redis.asyncio as redis

from app.database import get_async_db
from app.models.user import User, UserSession, UserRole, AuditLog
from app.schemas.user import UserCreate
from app.core.security import (
    verify_password, 
    get_password_hash, 
    verify_token,
    generate_session_token,
    oauth2_scheme
)
from app.config import settings
from app.core.logging import log_audit_event

# Redis client for session management
redis_client = redis.from_url(settings.REDIS_URL)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email address.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Get user by ID.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    Get user by username.
    """
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create a new user.
    """
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
        role=user_data.role if user_data.role else UserRole.CUSTOMER,
        is_active=True,
        is_verified=False
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Log user creation
    await log_audit_event(
        db=db,
        user_id=str(db_user.id),
        action="user_created",
        resource_type="user",
        resource_id=str(db_user.id),
        new_values={
            "email": db_user.email,
            "username": db_user.username,
            "role": db_user.role.value,
            "is_active": db_user.is_active
        }
    )
    
    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate user with email and password.
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        # Increment failed login attempts
        await increment_failed_login_attempts(db, user.id)
        return None
    
    # Reset failed login attempts on successful login
    await reset_failed_login_attempts(db, user.id)
    
    return user


async def create_user_session(
    db: AsyncSession,
    user_id: str,
    ip_address: str,
    user_agent: str,
    access_token: str,
    refresh_token: str = None
) -> UserSession:
    """
    Create a new user session.
    """
    session_token = generate_session_token()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    db_session = UserSession(
        user_id=user_id,
        session_token=session_token,
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    
    # Store session in Redis for quick access
    await redis_client.setex(
        f"session:{session_token}",
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id
    )
    
    return db_session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
        # Check if token is blacklisted
        if await is_token_blacklisted(token):
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check).
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def require_role(required_roles: list[UserRole]):
    """
    Dependency to require specific user roles.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


# Role-specific dependencies
require_admin = require_role([UserRole.ADMIN])
require_risk_officer = require_role([UserRole.ADMIN, UserRole.RISK_OFFICER])
require_loan_officer = require_role([UserRole.ADMIN, UserRole.RISK_OFFICER, UserRole.LOAN_OFFICER])
require_staff = require_role([UserRole.ADMIN, UserRole.RISK_OFFICER, UserRole.LOAN_OFFICER, UserRole.SUPPORT])


async def update_user_last_login(db: AsyncSession, user_id: str, ip_address: str):
    """
    Update user's last login timestamp.
    """
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_login=datetime.utcnow())
    )
    await db.commit()
    
    # Log login event
    await log_audit_event(
        db=db,
        user_id=user_id,
        action="user_login",
        resource_type="user",
        resource_id=user_id,
        additional_data={"ip_address": ip_address}
    )


async def update_user_password(db: AsyncSession, user_id: str, hashed_password: str):
    """
    Update user's password.
    """
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            hashed_password=hashed_password,
            password_changed_at=datetime.utcnow()
        )
    )
    await db.commit()


async def increment_failed_login_attempts(db: AsyncSession, user_id: str):
    """
    Increment failed login attempts and lock account if necessary.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return
    
    new_attempts = user.failed_login_attempts + 1
    should_lock = new_attempts >= 5  # Lock after 5 failed attempts
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            failed_login_attempts=new_attempts,
            is_locked=should_lock
        )
    )
    await db.commit()
    
    if should_lock:
        await log_audit_event(
            db=db,
            user_id=user_id,
            action="account_locked",
            resource_type="user",
            resource_id=user_id,
            additional_data={"reason": "too_many_failed_attempts"}
        )


async def reset_failed_login_attempts(db: AsyncSession, user_id: str):
    """
    Reset failed login attempts on successful login.
    """
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(failed_login_attempts=0)
    )
    await db.commit()


async def blacklist_token(token: str):
    """
    Add token to blacklist (Redis).
    """
    payload = verify_token(token)
    if payload and payload.get("exp"):
        exp_timestamp = payload["exp"]
        current_timestamp = datetime.utcnow().timestamp()
        ttl = int(exp_timestamp - current_timestamp)
        
        if ttl > 0:
            await redis_client.setex(f"blacklist:{token}", ttl, "true")


async def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted.
    """
    result = await redis_client.get(f"blacklist:{token}")
    return result is not None


async def logout_user(db: AsyncSession, user_id: str, token: str):
    """
    Logout user and blacklist token.
    """
    # Blacklist the token
    await blacklist_token(token)
    
    # Deactivate user sessions
    await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id)
        .where(UserSession.is_active == True)
        .values(is_active=False)
    )
    await db.commit()
    
    # Log logout event
    await log_audit_event(
        db=db,
        user_id=user_id,
        action="user_logout",
        resource_type="user",
        resource_id=user_id
    )


async def get_user_sessions(db: AsyncSession, user_id: str) -> list[UserSession]:
    """
    Get all active sessions for a user.
    """
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == user_id)
        .where(UserSession.is_active == True)
        .order_by(UserSession.created_at.desc())
    )
    return result.scalars().all()


async def revoke_user_session(db: AsyncSession, session_id: str, user_id: str):
    """
    Revoke a specific user session.
    """
    await db.execute(
        update(UserSession)
        .where(UserSession.id == session_id)
        .where(UserSession.user_id == user_id)
        .values(is_active=False)
    )
    await db.commit()
    
    # Remove from Redis
    session = await db.execute(
        select(UserSession).where(UserSession.id == session_id)
    )
    session_obj = session.scalar_one_or_none()
    if session_obj:
        await redis_client.delete(f"session:{session_obj.session_token}")