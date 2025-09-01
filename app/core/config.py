"""
Application configuration settings
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "OOUX ORCA Project Builder"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://ooux_user:ooux_password@localhost:5432/ooux_orca",
        description="Database connection URL"
    )
    TEST_DATABASE_URL: str = Field(
        default="postgresql://ooux_user:ooux_password@localhost:5432/ooux_orca_test",
        description="Test database connection URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Security & Authentication
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-this-in-production",
        description="Secret key for JWT tokens and session encryption"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Password Reset Settings
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    
    # Rate Limiting Configuration
    LOGIN_RATE_LIMIT_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_MINUTES: int = 1
    PASSWORD_RESET_RATE_LIMIT_ATTEMPTS: int = 3
    PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES: int = 5
    
    # Session Management
    SESSION_EXPIRE_MINUTES: int = 30
    MAX_SESSIONS_PER_USER: int = 5
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080"
    ]
    
    # File handling
    UPLOAD_DIR: str = "./uploads"
    EXPORT_DIR: str = "./exports"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    EXPORT_CLEANUP_HOURS: int = 24
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 1000
    
    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP server hostname")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    
    # Email Templates and Settings
    EMAILS_FROM_EMAIL: str = Field(
        default="noreply@ooux-orca.com",
        description="From email address for system emails"
    )
    EMAILS_FROM_NAME: str = Field(
        default="OOUX ORCA",
        description="From name for system emails"
    )
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 1
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    
    # Email Development Settings
    EMAIL_TEST_USER: Optional[str] = Field(
        default=None,
        description="Test email recipient for development"
    )
    USE_EMAIL_CONSOLE_BACKEND: bool = Field(
        default=True,
        description="Use console backend for emails in development"
    )
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Authentication Rate Limiting
    AUTH_RATE_LIMIT_ENABLED: bool = True
    REGISTRATION_RATE_LIMIT_PER_HOUR: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
