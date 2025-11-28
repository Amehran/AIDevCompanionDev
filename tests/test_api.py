
import pytest
from main import app

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


def test_chat_fast_mode(client):
    """Test POST /chat?fast=true returns stub response without invoking LLM."""
    response = client.post("/chat?fast=true", json={"source_code": "print('hello')"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "OK (fast mode)"
    assert data["issues"] == []


def test_chat_missing_code(client):
    """Test POST /chat without source_code returns 400 (InvalidInput)."""
    response = client.post("/chat", json={})
    assert response.status_code == 400

