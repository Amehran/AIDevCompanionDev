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
        body = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            result = json.loads(response["body"].read())
            # Claude returns 'completion' key
            return result.get("completion", "")
        except Exception as e:
            logger.error(f"Bedrock invocation failed: {e}")
            raise
