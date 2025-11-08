"""Dependency injection container for service singletons."""
from app.core.config import settings, Settings, get_settings  # re-export
from app.services.rate_limiter import RateLimiter
from app.services.job_manager import JobManager

# Instantiate singletons
rate_limiter = RateLimiter(settings.rate_limit_per_minute)
job_manager = JobManager()

# Provider helpers (FastAPI Depends can use these if needed)

def get_rate_limiter() -> RateLimiter:
    return rate_limiter

def get_job_manager() -> JobManager:
    return job_manager

__all__ = [
    "settings",
    "Settings",
    "get_settings",
    "rate_limiter",
    "job_manager",
    "get_rate_limiter",
    "get_job_manager",
]
