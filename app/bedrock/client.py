import boto3
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BedrockClient:
    def __init__(self, model_id: Optional[str] = None):
        self.client = boto3.client("bedrock-runtime")
        # Default to Claude 3 Sonnet if not specified
        self.model_id = model_id or "anthropic.claude-3-sonnet-20240229-v1:0"

    def invoke(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        # Claude 3 models require the Messages API
        body = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "anthropic_version": "bedrock-2023-05-31"
        }
        try:
            response_stream = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            # Parse streaming response correctly
            completion = ""
            for event in response_stream["body"]:
                chunk = json.loads(event["chunk"]["bytes"])
                
                if chunk["type"] == "content_block_delta":
                    if "delta" in chunk:
                        completion += chunk["delta"].get("text", "")
                        
            return completion
        except Exception as e:
            logger.error(f"Bedrock invocation failed: {e}")
            raise
