from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.schemas.user import UserResponse, UserCreate, PasswordChange, PasswordReset, PasswordResetConfirm


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    mfa_token: Optional[str] = Field(None, min_length=6, max_length=6)
    remember_me: bool = False


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    requires_mfa: bool = False


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserResponse] = None


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    scopes: list[str] = []


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    everywhere: bool = False  # Logout from all devices


class SecurityEventLog(BaseModel):
    id: str
    user_id: Optional[str]
    event_type: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool
    details: Optional[Dict[str, Any]]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AuditLogEntry(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    additional_data: Optional[Dict[str, Any]]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    logs: list[AuditLogEntry]
    total: int
    page: int
    size: int
    pages: int


class PermissionCheck(BaseModel):
    resource: str
    action: str
    resource_id: Optional[str] = None


class PermissionResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None


class SecuritySettings(BaseModel):
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = True
    password_expiry_days: int = 90
    session_timeout_minutes: int = 30
    max_failed_login_attempts: int = 5
    account_lockout_duration_minutes: int = 30
    mfa_required_for_admin: bool = True
    mfa_required_for_sensitive_operations: bool = True


class SecuritySettingsUpdate(BaseModel):
    password_min_length: Optional[int] = None
    password_require_uppercase: Optional[bool] = None
    password_require_lowercase: Optional[bool] = None
    password_require_numbers: Optional[bool] = None
    password_require_symbols: Optional[bool] = None
    password_expiry_days: Optional[int] = None
    session_timeout_minutes: Optional[int] = None
    max_failed_login_attempts: Optional[int] = None
    account_lockout_duration_minutes: Optional[int] = None
    mfa_required_for_admin: Optional[bool] = None
    mfa_required_for_sensitive_operations: Optional[bool] = None