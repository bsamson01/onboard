import logging
import logging.config
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings


def setup_logging():
    """Set up application logging configuration."""
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Logging configuration
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": settings.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter" if settings.LOG_LEVEL == "INFO" else "logging.Formatter",
            },
        },
        "handlers": {
            "console": {
                "level": settings.LOG_LEVEL,
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": sys.stdout,
            },
            "file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "detailed",
                "filename": "logs/errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "audit_file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": "logs/audit.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8",
            },
        },
        "loggers": {
            # Root logger
            "": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            # Application loggers
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            # Audit logger for security events
            "app.audit": {
                "level": "INFO",
                "handlers": ["audit_file", "console"],
                "propagate": False,
            },
            # Database logger
            "sqlalchemy.engine": {
                "level": "WARNING" if not settings.DEBUG else "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            # Celery logger
            "celery": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            # External services logger
            "httpx": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            # Uvicorn logger
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
        },
    }
    
    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Set up additional loggers for specific modules
    setup_security_logger()


def setup_security_logger():
    """Set up security-specific logging."""
    security_logger = logging.getLogger("app.security")
    
    # Create security log handler
    security_handler = logging.handlers.RotatingFileHandler(
        "logs/security.log",
        maxBytes=10485760,  # 10MB
        backupCount=10,
        encoding="utf8"
    )
    
    security_formatter = logging.Formatter(
        "%(asctime)s - SECURITY - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    security_handler.setFormatter(security_formatter)
    
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name or "app")


# This function moved to log_audit_event_file at the end of the file


def log_security_event(event_type: str, ip_address: Optional[str] = None, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    """Log a security event."""
    security_logger = logging.getLogger("app.security")
    
    security_data = {
        "event_type": event_type,
        "ip_address": ip_address,
        "user_id": user_id,
        "details": details or {}
    }
    
    security_logger.warning(f"SECURITY: {event_type} from {ip_address or 'unknown'}", extra=security_data)


# Pre-configure some useful loggers
class SecurityEvent:
    """Security event types for consistent logging."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_LOCKED = "login_locked"
    PASSWORD_CHANGED = "password_changed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_EXPORT = "data_export"
    ADMIN_ACTION = "admin_action"


class AuditEvent:
    """Audit event types for consistent logging."""
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_UPDATED = "customer_updated"
    APPLICATION_SUBMITTED = "application_submitted"
    APPLICATION_APPROVED = "application_approved"
    APPLICATION_REJECTED = "application_rejected"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_VERIFIED = "document_verified"
    SCORE_CALCULATED = "score_calculated"
    ALERT_CREATED = "alert_created"
    REPORT_GENERATED = "report_generated"


async def log_audit_event(
    db: AsyncSession,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
):
    """
    Log an audit event to the database.
    This function is used by the core modules for database audit logging.
    """
    from app.models.user import AuditLog
    
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=additional_data
        )
        
        db.add(audit_log)
        await db.commit()
        
        # Also log to the file-based audit log
        log_audit_event_file(action, user_id, {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "old_values": old_values,
            "new_values": new_values,
            "ip_address": ip_address,
            "additional_data": additional_data
        })
        
    except Exception as e:
        # If database logging fails, at least log to file
        logger = get_logger("app.audit")
        logger.error(f"Failed to log audit event to database: {e}")
        log_audit_event_file(action, user_id, {
            "error": str(e),
            "resource_type": resource_type,
            "resource_id": resource_id
        })


def log_audit_event_file(event_type: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    """Log an audit event to file (renamed from original log_audit_event)."""
    audit_logger = logging.getLogger("app.audit")
    
    audit_data = {
        "event_type": event_type,
        "user_id": user_id,
        "details": details or {}
    }
    
    audit_logger.info(f"AUDIT: {event_type}", extra=audit_data)