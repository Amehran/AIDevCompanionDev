import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

@pytest.fixture
def mock_swarm():
    with patch("app.services.agents.KotlinAnalysisSwarm") as MockSwarm:
        instance = MockSwarm.return_value
        # Configure analyze to be awaitable
        future = asyncio.Future()
        future.set_result({
            "summary": "Integration Test Summary",
            "issues": [
                {
                    "type": "SECURITY",
                    "description": "Test Security Issue",
                    "suggestion": "Fix it"
                }
            ]
        })
        instance.analyze.return_value = future
        yield instance

def test_chat_endpoint_success(mock_swarm):
    response = client.post("/chat", json={"source_code": "fun main() {}"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Integration Test Summary"
    assert len(data["issues"]) == 1
    assert data["issues"][0]["type"] == "SECURITY"
    assert "conversation_id" in data

def test_chat_endpoint_fast_mode():
    response = client.post("/chat?fast=true", json={"source_code": "fun main() {}"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "OK (fast mode)"
    assert data["issues"] == []

def test_chat_endpoint_invalid_input():
    response = client.post("/chat", json={})
    assert response.status_code == 400  # InvalidInput raises 400
