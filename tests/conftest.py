"""
Shared pytest fixtures for all test modules.
"""

import pytest
import asyncio
import httpx
import os

# Set test environment variables before any imports
os.environ.setdefault("BEDROCK_API_KEY", "test-bedrock-key")
os.environ.setdefault("BEDROCK_REGION", "us-east-1")
os.environ.setdefault("MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")


class TestClient:
    """Sync wrapper around httpx.AsyncClient+ASGITransport for compatibility."""
    def __init__(self, app, base_url: str = "http://testserver") -> None:
        self.app = app
        self.base_url = base_url

    def request(self, method: str, url: str, **kwargs):
        async def _do():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self.app), base_url=self.base_url
            ) as ac:
                return await ac.request(method, url, **kwargs)

        return asyncio.run(_do())

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.request("DELETE", url, **kwargs)


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    """Reset global state before each test."""
    # Set test environment variables
    monkeypatch.setenv("BEDROCK_API_KEY", "test-bedrock-key")
    monkeypatch.setenv("BEDROCK_REGION", "us-east-1")
    monkeypatch.setenv("MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    
    from app.core.config import settings as _settings
    from app.core import di
    from app.services.rate_limiter import RateLimiter
    from main import _jobs, _jobs_lock

    # Configure settings for tests
    _settings.rate_limit_per_minute = 5
    _settings.max_concurrent_jobs = 3

    # Reinstantiate services for clean state
    di.rate_limiter = RateLimiter(_settings.rate_limit_per_minute)
    
    # Import and reset conversation manager if it exists
    try:
        from app.services.conversation_manager import ConversationManager
        di.conversation_manager = ConversationManager()
    except (ImportError, AttributeError):
        pass  # Not all tests need conversation manager

    with _jobs_lock:
        _jobs.clear()
    with di.rate_limiter._lock:
        di.rate_limiter._buckets.clear()

    yield

    # Cleanup after test
    with _jobs_lock:
        _jobs.clear()
    with di.rate_limiter._lock:
        di.rate_limiter._buckets.clear()
    
    # Clear conversations if manager exists
    try:
        if hasattr(di, 'conversation_manager'):
            di.conversation_manager.clear_all()
    except (AttributeError, NameError):
        pass


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    from main import app
    return TestClient(app)
