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
    # Prepare mock response
    expected_completion = "This is a test completion."
    response_body = {
        "completion": expected_completion
    }
    stubber.add_response(
        "invoke_model",
        {"body": io.BytesIO(bytes(json.dumps(response_body), "utf-8")), "contentType": "application/json"},
        {
            "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({"prompt": "test", "max_tokens": 1024, "temperature": 0.2})
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
