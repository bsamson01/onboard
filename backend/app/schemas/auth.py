from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole, UserState


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.CUSTOMER


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    is_locked: bool
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    mfa_enabled: bool = False
    profile_picture_url: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    user_state: UserState = UserState.REGISTERED
    onboarding_completed_at: Optional[datetime] = None
    last_profile_update: Optional[datetime] = None
    profile_expiry_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8) 