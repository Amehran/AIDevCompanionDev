import boto3
import json
import logging
from typing import Optional, Dict, Any, List

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

    async def chat(
        self, 
        user_message: str, 
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> str:
        """
        Handle conversational chat with context awareness.
        
        Args:
            user_message: The user's question or message
            context: Optional context including code, issues, and conversation history
            max_tokens: Maximum tokens for response
            temperature: Temperature for response generation (higher = more creative)
            
        Returns:
            AI-generated response
        """
        # Build context-aware prompt
        system_prompt = """You are an AI assistant helping developers understand their Kotlin code analysis results. 
You provide clear, concise, and helpful explanations about code quality, security issues, and performance concerns.
When answering questions, reference the specific code and issues that were analyzed."""

        # Add context if available
        context_parts = []
        if context:
            if context.get("original_code"):
                context_parts.append(f"Analyzed Code:\n```kotlin\n{context['original_code']}\n```")
            
            if context.get("detected_issues"):
                issues_text = "\n".join([
                    f"- {issue.type}: {issue.description}" 
                    for issue in context["detected_issues"]
                ])
                context_parts.append(f"Detected Issues:\n{issues_text}")
            
            if context.get("conversation_history"):
                # Include last few messages for context
                history = context["conversation_history"][-3:]  # Last 3 messages
                history_text = "\n".join([
                    f"{msg.role}: {msg.content}"
                    for msg in history
                ])
                context_parts.append(f"Recent Conversation:\n{history_text}")

        # Combine context and user message
        full_prompt = system_prompt
        if context_parts:
            full_prompt += "\n\n" + "\n\n".join(context_parts)
        full_prompt += f"\n\nUser Question: {user_message}\n\nPlease provide a helpful and specific answer:"

        # Use run_in_threadpool to make synchronous invoke work in async context
        try:
            from starlette.concurrency import run_in_threadpool
            response = await run_in_threadpool(
                self.invoke,
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response
        except Exception as e:
            logger.error(f"Chat invocation failed: {e}")
            return f"I apologize, but I encountered an error processing your question. Please try again."
