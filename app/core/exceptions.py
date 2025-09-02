"""
Custom exception classes for the application
"""

from typing import Optional, Dict, Any


class AppException(Exception):
    """Base exception class for application-specific exceptions"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppException):
    """Raised when validation fails"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.field = field
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message, status_code=400, details=details)


class PermissionError(AppException):
    """Raised when user lacks required permissions"""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
        user_role: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if required_permission:
            details["required_permission"] = required_permission
        if user_role:
            details["user_role"] = user_role
        super().__init__(message, status_code=403, details=details)


class NotFoundError(AppException):
    """Raised when a resource is not found"""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, status_code=404, details=details)


class ConflictError(AppException):
    """Raised when there's a conflict with existing data"""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        conflicting_field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if conflicting_field:
            details["conflicting_field"] = conflicting_field
        super().__init__(message, status_code=409, details=details)


class AuthenticationError(AppException):
    """Raised when authentication fails"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=401, details=details)


class RateLimitError(AppException):
    """Raised when rate limit is exceeded"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status_code=429, details=details)


class BusinessRuleError(AppException):
    """Raised when a business rule is violated"""
    
    def __init__(
        self,
        message: str = "Business rule violation",
        rule_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if rule_name:
            details["rule_name"] = rule_name
        super().__init__(message, status_code=400, details=details)


class ExternalServiceError(AppException):
    """Raised when an external service fails"""
    
    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if service_name:
            details["service_name"] = service_name
        super().__init__(message, status_code=502, details=details)
