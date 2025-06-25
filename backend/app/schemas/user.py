from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from enum import Enum

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = UserRole.CUSTOMER
    timezone: Optional[str] = "UTC"
    language: Optional[str] = "en"


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v
    
    @validator("username")
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must contain only letters, numbers, hyphens, and underscores")
        return v


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    timezone: Optional[str] = None
    language: Optional[str] = None
    profile_picture_url: Optional[str] = None


class UserUpdateAdmin(UserUpdate):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_locked: Optional[bool] = None


class UserInDB(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    is_locked: bool
    mfa_enabled: bool
    failed_login_attempts: int
    last_login: Optional[datetime]
    password_changed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    full_name: str
    phone_number: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    is_locked: bool
    mfa_enabled: bool
    last_login: Optional[datetime]
    timezone: str
    language: str
    profile_picture_url: Optional[str]
    created_at: datetime
    
    # Role-based properties
    is_admin: bool
    is_risk_officer: bool
    is_loan_officer: bool
    is_support: bool
    is_customer: bool
    can_access_admin: bool
    can_access_risk: bool
    can_access_loans: bool
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class UserSessionResponse(BaseModel):
    id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_active: bool
    expires_at: datetime
    created_at: datetime
    last_activity: datetime
    
    class Config:
        from_attributes = True


class UserSessionsResponse(BaseModel):
    sessions: List[UserSessionResponse]
    total: int


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator("confirm_new_password")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("New passwords do not match")
        return v


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class MFASetup(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]


class MFAVerify(BaseModel):
    token: str = Field(..., min_length=6, max_length=6)


class MFABackupCode(BaseModel):
    code: str = Field(..., min_length=8, max_length=8)