"""Minimal exceptions for API validation."""

class AppException(Exception):
    """Base exception for application errors with status codes."""
    status_code = 500
    
    def to_dict(self):
        """Convert exception to dictionary for JSON responses."""
        return {
            "error": {
                "type": self.__class__.__name__,
                "message": str(self)
            }
        }


class InvalidInput(AppException):
    """Raised when request input is missing or invalid."""
    status_code = 400


class RateLimitExceeded(AppException):
    """Raised when rate limit is exceeded."""
    status_code = 429
    
    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after:.1f} seconds")
    
    def to_dict(self):
        """Include retry_after in response."""
        data = super().to_dict()
        data["retry_after"] = self.retry_after
        return data


class ServerBusy(AppException):
    """Raised when server has too many concurrent jobs."""
    status_code = 503
    
    def __init__(self, active_jobs: int, max_concurrent: int):
        self.active_jobs = active_jobs
        self.max_concurrent = max_concurrent
        super().__init__(f"Server busy: {active_jobs}/{max_concurrent} jobs active")


class JobNotFound(AppException):
    """Raised when a job ID is not found."""
    status_code = 404
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")
