import logging
import traceback
from typing import Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels for logging and monitoring"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better organization"""
    VALIDATION = "validation"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    EXTERNAL_SERVICE = "external_service"
    CACHE = "cache"
    ML_MODEL = "ml_model"
    EMBEDDING = "embedding"
    RECOMMENDATION = "recommendation"
    SYSTEM = "system"

class BaseAppException(Exception):
    """Base exception class for the application"""
    
    def __init__(
        self,
        message: str,
        error_code: str = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        details: Dict[str, Any] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.category = category
        self.details = details or {}
        self.user_id = user_id
        self.request_id = request_id
        self.timestamp = datetime.utcnow()
        
        # Log the exception with standardized format
        self._log_exception()
    
    def _log_exception(self):
        """Log exception with standardized format"""
        log_data = {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "request_id": self.request_id,
            "details": self.details,
            "traceback": traceback.format_exc()
        }
        
        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"[CRITICAL] {self.error_code}: {self.message}", extra=log_data)
        elif self.severity == ErrorSeverity.HIGH:
            logger.error(f"[ERROR] {self.error_code}: {self.message}", extra=log_data)
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"[WARNING] {self.error_code}: {self.message}", extra=log_data)
        else:
            logger.info(f"[INFO] {self.error_code}: {self.message}", extra=log_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }

class ValidationException(BaseAppException):
    """Exception for validation errors"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            details=details,
            **kwargs
        )

class NotFoundException(BaseAppException):
    """Exception for resource not found"""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Union[str, int],
        **kwargs
    ):
        message = f"{resource_type} with ID {resource_id} not found"
        details = {
            "resource_type": resource_type,
            "resource_id": str(resource_id)
        }
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.SYSTEM,
            details=details,
            **kwargs
        )

class DatabaseException(BaseAppException):
    """Exception for database errors"""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            details=details,
            **kwargs
        )

class AuthenticationException(BaseAppException):
    """Exception for authentication errors"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.AUTHENTICATION,
            **kwargs
        )

class AuthorizationException(BaseAppException):
    """Exception for authorization errors"""
    
    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if required_permission:
            details["required_permission"] = required_permission
        
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.AUTHORIZATION,
            details=details,
            **kwargs
        )

class CacheException(BaseAppException):
    """Exception for cache errors"""
    
    def __init__(
        self,
        message: str,
        cache_operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if cache_operation:
            details["cache_operation"] = cache_operation
        
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.CACHE,
            details=details,
            **kwargs
        )

class MLModelException(BaseAppException):
    """Exception for ML model errors"""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if model_name:
            details["model_name"] = model_name
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="ML_MODEL_ERROR",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.ML_MODEL,
            details=details,
            **kwargs
        )

class EmbeddingException(BaseAppException):
    """Exception for embedding generation errors"""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        text_length: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if model_name:
            details["model_name"] = model_name
        if text_length is not None:
            details["text_length"] = text_length
        
        super().__init__(
            message=message,
            error_code="EMBEDDING_ERROR",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EMBEDDING,
            details=details,
            **kwargs
        )

class RecommendationException(BaseAppException):
    """Exception for recommendation engine errors"""
    
    def __init__(
        self,
        message: str,
        algorithm: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if algorithm:
            details["algorithm"] = algorithm
        if user_id:
            details["user_id"] = user_id
        
        super().__init__(
            message=message,
            error_code="RECOMMENDATION_ERROR",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.RECOMMENDATION,
            details=details,
            **kwargs
        )

def handle_exception(
    exc: Exception,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> BaseAppException:
    """Convert generic exceptions to application exceptions"""
    
    if isinstance(exc, BaseAppException):
        return exc
    
    # Convert common exceptions
    if isinstance(exc, ValueError):
        return ValidationException(str(exc), user_id=user_id, request_id=request_id)
    elif isinstance(exc, KeyError):
        return ValidationException(f"Missing required field: {exc}", user_id=user_id, request_id=request_id)
    elif isinstance(exc, TypeError):
        return ValidationException(f"Invalid type: {exc}", user_id=user_id, request_id=request_id)
    else:
        return BaseAppException(
            message=str(exc),
            error_code="UNKNOWN_ERROR",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            user_id=user_id,
            request_id=request_id
        )

def exception_to_http_exception(exc: BaseAppException) -> HTTPException:
    """Convert application exception to HTTP exception"""
    
    status_code_map = {
        ValidationException: status.HTTP_400_BAD_REQUEST,
        NotFoundException: status.HTTP_404_NOT_FOUND,
        DatabaseException: status.HTTP_500_INTERNAL_SERVER_ERROR,
        AuthenticationException: status.HTTP_401_UNAUTHORIZED,
        AuthorizationException: status.HTTP_403_FORBIDDEN,
        CacheException: status.HTTP_503_SERVICE_UNAVAILABLE,
        MLModelException: status.HTTP_503_SERVICE_UNAVAILABLE,
        EmbeddingException: status.HTTP_503_SERVICE_UNAVAILABLE,
        RecommendationException: status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    
    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPException(
        status_code=status_code,
        detail=exc.to_dict()
    )
