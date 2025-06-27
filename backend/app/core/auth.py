from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_async_db
from app.models.user import User
from app.schemas.auth import UserCreate

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handler
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user in the database."""
    # Check if user already exists by email
    stmt = select(User).where(User.email == user_data.email)
    result = await session.execute(stmt)
    existing_user = result.scalar()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    stmt = select(User).where(User.username == user_data.username)
    result = await session.execute(stmt)
    existing_username = result.scalar()
    
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        # Extract user ID from token
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar()
    
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Check if user is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="User account is locked"
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (alias for get_current_user with additional checks)."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_role: str):
    """Decorator factory to require specific user roles."""
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        return current_user
    return role_dependency


def require_roles(required_roles: list):
    """Decorator factory to require one of multiple user roles."""
    def roles_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}"
            )
        return current_user
    return roles_dependency


# Convenience role dependencies
require_admin = require_role("admin")
require_risk_officer = require_roles(["admin", "risk_officer"])
require_loan_officer = require_roles(["admin", "risk_officer", "loan_officer"])
require_staff = require_roles(["admin", "risk_officer", "loan_officer", "support"])


async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password."""
    # Get user by email
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalar()
    
    if not user:
        return None
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.is_locked = True
        
        # Let the dependency injection handle the commit
        return None
    
    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.last_login = datetime.now()
    # Let the dependency injection handle the commit
    
    return user