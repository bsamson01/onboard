from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Database
    DATABASE_URL: str = "postgresql://scorecard_user:scorecard_pass@localhost:5432/scorecard_db"
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Credit Scorecard Microservice"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Service
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Scorecard Settings
    MAX_SCORECARD_VERSIONS: int = 100
    DEFAULT_SCORE_RANGE: tuple = (300, 850)  # Like FICO scores
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()