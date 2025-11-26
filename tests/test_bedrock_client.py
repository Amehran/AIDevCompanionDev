import pytest
from app.bedrock.client import BedrockClient
import boto3
from botocore.stub import Stubber
import json
import io

@pytest.fixture
def bedrock_stub():
    client = boto3.client("bedrock-runtime")
    stubber = Stubber(client)
    yield client, stubber
    stubber.deactivate()


def test_bedrock_invoke_success(monkeypatch, bedrock_stub):
    client, stubber = bedrock_stub
    # Prepare mock streaming response for invoke_model_with_response_stream
    expected_completion = "This is a test completion."
    # Simulate the streaming response structure as a dict for body
    streaming_body = {
        "chunk": {
            "bytes": json.dumps({"contentBlock": {"text": expected_completion}}).encode()
        }
    }
    stubber.add_response(
        "invoke_model_with_response_stream",
        {"body": streaming_body, "contentType": "application/json"},
        {
            "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1024,
                "temperature": 0.2,
                "anthropic_version": "bedrock-2023-05-31"
            })
        }
    )
    stubber.activate()

    # Patch boto3 client in BedrockClient to use stub
    monkeypatch.setattr("boto3.client", lambda service: client)
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
