from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os
from decouple import config


class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = config("DATABASE_URL", default="sqlite:///./app.db")
    ASYNC_DATABASE_URL: str = config("ASYNC_DATABASE_URL", default="sqlite+aiosqlite:///./app.db")
    
    # Redis Configuration
    REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = config("CELERY_BROKER_URL", default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
    
    # Security Configuration
    SECRET_KEY: str = config("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
    REFRESH_TOKEN_EXPIRE_DAYS: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7, cast=int)
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    
    # Application Configuration
    DEBUG: bool = config("DEBUG", default=False, cast=bool)
    API_V1_STR: str = config("API_V1_STR", default="/api/v1")
    PROJECT_NAME: str = config("PROJECT_NAME", default="Microfinance Platform")
    VERSION: str = config("VERSION", default="1.0.0")
    DESCRIPTION: str = config("DESCRIPTION", default="Modular Microfinance Onboarding & Loan Management Platform")
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = config("MAX_FILE_SIZE", default=10485760, cast=int)  # 10MB
    UPLOAD_DIR: str = config("UPLOAD_DIR", default="./uploads")
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png", "doc", "docx"]
    
    # OCR Configuration
    TESSERACT_CMD: str = config("TESSERACT_CMD", default="/usr/bin/tesseract")
    OCR_LANGUAGES: str = config("OCR_LANGUAGES", default="eng")
    
    # External Services
    SCORECARD_API_URL: str = config("SCORECARD_API_URL", default="http://localhost:8001")
    SCORECARD_API_KEY: str = config("SCORECARD_API_KEY", default="")
    
    # Email Configuration
    MAIL_USERNAME: Optional[str] = config("MAIL_USERNAME", default=None)
    MAIL_PASSWORD: Optional[str] = config("MAIL_PASSWORD", default=None)
    MAIL_FROM: str = config("MAIL_FROM", default="noreply@microfinance.com")
    MAIL_PORT: int = config("MAIL_PORT", default=587, cast=int)
    MAIL_SERVER: str = config("MAIL_SERVER", default="smtp.gmail.com")
    MAIL_FROM_NAME: str = config("MAIL_FROM_NAME", default="Microfinance Platform")
    MAIL_STARTTLS: bool = config("MAIL_STARTTLS", default=True, cast=bool)
    MAIL_SSL_TLS: bool = config("MAIL_SSL_TLS", default=False, cast=bool)
    
    # SMS Configuration (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = config("TWILIO_ACCOUNT_SID", default=None)
    TWILIO_AUTH_TOKEN: Optional[str] = config("TWILIO_AUTH_TOKEN", default=None)
    TWILIO_PHONE_NUMBER: Optional[str] = config("TWILIO_PHONE_NUMBER", default=None)
    
    # Logging Configuration
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")
    LOG_FORMAT: str = config("LOG_FORMAT", default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = config("RATE_LIMIT_PER_MINUTE", default=60, cast=int)
    RATE_LIMIT_BURST: int = config("RATE_LIMIT_BURST", default=10, cast=int)
    
    # Monitoring
    ENABLE_METRICS: bool = config("ENABLE_METRICS", default=True, cast=bool)
    METRICS_PORT: int = config("METRICS_PORT", default=8001, cast=int)
    
    class Config:
        case_sensitive = True
        env_file = ".env"


# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)