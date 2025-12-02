import pytest
from app.bedrock.client import BedrockClient
import boto3
from botocore.stub import Stubber
import json
import io
from unittest.mock import MagicMock
@pytest.fixture
def bedrock_stub():
    client = boto3.client("bedrock-runtime")
    stubber = Stubber(client)
    yield client, stubber
    stubber.deactivate()


def test_bedrock_invoke_success(monkeypatch):
    # Mock boto3 client directly
    mock_client = MagicMock()
    
    expected_completion = "This is a test completion."
    
    # Mock response stream
    # The client iterates over response['body']
    # Each item in body is an event dict
    event = {
        "chunk": {
            "bytes": json.dumps({
                "type": "content_block_delta",
                "delta": {"text": expected_completion}
            }).encode()
        }
    }
    
    mock_client.invoke_model_with_response_stream.return_value = {
        "body": [event]
    }

    monkeypatch.setattr("boto3.client", lambda service: mock_client)
    
    bedrock = BedrockClient()
    result = bedrock.invoke("test")
    assert result == expected_completion


def test_bedrock_invoke_error(monkeypatch, bedrock_stub):
    client, stubber = bedrock_stub
    stubber.add_client_error("invoke_model")
    stubber.activate()
    monkeypatch.setattr("boto3.client", lambda service: client)
    bedrock = BedrockClient()
    with pytest.raises(Exception):
        bedrock.invoke("test")
