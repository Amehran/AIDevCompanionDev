import pytest
from unittest.mock import MagicMock, patch
from app.services.agents import KotlinAnalysisSwarm, Agent

@pytest.mark.asyncio
async def test_agent_analyze():
    # Mock BedrockClient
    with patch("app.services.agents.BedrockClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.invoke.return_value = '{"summary": "Good code", "issues": []}'
        
        agent = Agent("TestAgent", "Tester")
        result = await agent.analyze("val x = 1")
        
        assert result["summary"] == "Good code"
        assert result["issues"] == []
        mock_instance.invoke.assert_called_once()

@pytest.mark.asyncio
async def test_swarm_analyze():
    # Mock BedrockClient for all agents
    with patch("app.services.agents.BedrockClient") as MockClient:
        mock_instance = MockClient.return_value
        # Return different responses based on the prompt (simplified)
        mock_instance.invoke.return_value = '{"summary": "Analysis done", "issues": []}'
        
        swarm = KotlinAnalysisSwarm()
        result = await swarm.analyze("fun main() {}")
        
        assert result["summary"] == "Analysis done"
        assert isinstance(result["issues"], list)
        # 3 agents + 1 orchestrator = 4 calls
        assert mock_instance.invoke.call_count == 4
