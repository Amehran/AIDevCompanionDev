"""Core API tests for ai-dev-companion-backend."""

import pytest
import asyncio
import httpx

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

from main import app

@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


# =========================
# Basic Endpoint Tests
# =========================

def test_root_endpoint(client):
    """Test GET / returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "ai-dev-companion-backend" in response.json()["message"]


def test_test_endpoint(client):
    """Test POST /test returns ok status."""
    response = client.post("/test")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_echo_endpoint(client):
    """Test POST /echo returns payload verbatim."""
    payload = {"foo": "bar", "num": 42}
    response = client.post("/echo", json=payload)
    assert response.status_code == 200
    assert response.json() == {"received": payload}


def test_health_endpoint(client):
    """Test GET /health returns status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_diag_endpoint(client):
    """Test GET /diag returns diagnostic info."""
    response = client.get("/diag")
    assert response.status_code == 200
    data = response.json()
    assert "commit" in data  # diag returns "commit" not "commit_sha"


# =========================
# Chat Endpoint Tests
# =========================

def test_chat_stub_mode(client):
    """Test POST /chat returns minimal stub response for Android client."""
    response = client.post("/chat", json={"source_code": "print('hello')"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["summary"], str)
    assert data["summary"].startswith("Stub review OK")
    assert data["issues"] == []


def test_chat_missing_code(client):
    """Test POST /chat without source_code returns 422."""
    response = client.post("/chat", json={})
    assert response.status_code == 422
    assert "detail" in response.json()
