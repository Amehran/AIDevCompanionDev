import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from main import app

@pytest.fixture
def mock_swarm():
    with patch("app.services.agents.KotlinAnalysisSwarm") as MockSwarm:
        instance = MockSwarm.return_value
        # Configure analyze to be awaitable
        instance.analyze = AsyncMock(return_value={
            "summary": "Integration Test Summary",
            "issues": [
                {
                    "type": "SECURITY",
                    "description": "Test Security Issue",
                    "suggestion": "Fix it"
                }
            ]
        })
        yield instance

def test_chat_endpoint_success(client, mock_swarm):
    response = client.post("/chat", json={"source_code": "fun main() {}"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Integration Test Summary"
    assert len(data["issues"]) == 1
    assert data["issues"][0]["type"] == "SECURITY"
    assert "conversation_id" in data

def test_chat_endpoint_fast_mode(client):
    response = client.post("/chat?fast=true", json={"source_code": "fun main() {}"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "OK (fast mode)"
    assert data["issues"] == []

def test_chat_endpoint_invalid_input(client):
    response = client.post("/chat", json={})
    assert response.status_code == 400  # InvalidInput raises 400
