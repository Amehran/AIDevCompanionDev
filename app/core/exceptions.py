"""Minimal exceptions for API validation."""

class InvalidInput(Exception):
    """Raised when request input is missing or invalid."""
    pass


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after:.1f} seconds")


class ServerBusy(Exception):
    """Raised when server has too many concurrent jobs."""
    def __init__(self, active_jobs: int, max_concurrent: int):
        self.active_jobs = active_jobs
        self.max_concurrent = max_concurrent
        super().__init__(f"Server busy: {active_jobs}/{max_concurrent} jobs active")


class JobNotFound(Exception):
    """Raised when a job ID is not found."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")
