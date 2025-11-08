"""
Custom exceptions for the application.

These exceptions provide structured error handling with consistent
error responses across the API.
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """
    Base exception for all application errors.
    
    All custom exceptions should inherit from this class.
    This allows for consistent error handling and structured error responses.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_type: str = "internal_error",
        details: Optional[Any] = None
    ):
        """
        Initialize application exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_type: Machine-readable error type identifier
            details: Additional error details (optional)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for JSON response.
        
        Returns:
            Dictionary with error details in structured format
        """
        error_dict = {
            "error": {
                "type": self.error_type,
                "message": self.message,
            }
        }
        
        if self.details is not None:
            error_dict["error"]["details"] = self.details
        
        return error_dict


class RateLimitExceeded(AppException):
    """
    Exception raised when rate limit is exceeded.
    
    Returns HTTP 429 (Too Many Requests) with retry_after information.
    """
    
    def __init__(self, retry_after: int):
        """
        Initialize rate limit exception.
        
        Args:
            retry_after: Number of seconds until the client can retry
        """
        super().__init__(
            message=f"Too many requests. Try again in {retry_after} seconds.",
            status_code=429,
            error_type="rate_limit_exceeded",
            details=None
        )
        self.retry_after = retry_after
    
    def to_dict(self) -> Dict[str, Any]:
        """Add retry_after to error response."""
        result = super().to_dict()
        result["error"]["retry_after"] = self.retry_after
        return result


class ServerBusy(AppException):
    """
    Exception raised when server is at capacity.
    
    Returns HTTP 503 (Service Unavailable) when max concurrent jobs reached.
    """
    
    def __init__(self, active_jobs: int, max_concurrent: int):
        """
        Initialize server busy exception.
        
        Args:
            active_jobs: Number of currently active jobs
            max_concurrent: Maximum concurrent jobs allowed
        """
        super().__init__(
            message="Server is busy. Please try again shortly.",
            status_code=503,
            error_type="server_busy",
            details={
                "active_jobs": active_jobs,
                "max_concurrent": max_concurrent,
            }
        )
        self.active_jobs = active_jobs
        self.max_concurrent = max_concurrent


class CodeAnalysisError(AppException):
    """
    Exception raised when code analysis fails.
    
    Returns HTTP 500 with details about the analysis failure.
    """
    
    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize code analysis error.
        
        Args:
            message: Human-readable error message
            details: Technical details about the error (optional)
        """
        super().__init__(
            message=message,
            status_code=500,
            error_type="code_analysis_error",
            details=details
        )


class InvalidInput(AppException):
    """
    Exception raised when input validation fails.
    
    Returns HTTP 422 (Unprocessable Entity).
    """
    
    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize invalid input exception.
        
        Args:
            message: Human-readable error message
            field: Name of the invalid field (optional)
        """
        details = {"field": field} if field else None
        super().__init__(
            message=message,
            status_code=422,
            error_type="invalid_input",
            details=details
        )


class JobNotFound(AppException):
    """
    Exception raised when a job is not found.
    
    Returns HTTP 404 (Not Found).
    """
    
    def __init__(self, job_id: str):
        """
        Initialize job not found exception.
        
        Args:
            job_id: ID of the job that was not found
        """
        super().__init__(
            message=f"Job '{job_id}' not found.",
            status_code=404,
            error_type="job_not_found",
            details={"job_id": job_id}
        )
        self.job_id = job_id
