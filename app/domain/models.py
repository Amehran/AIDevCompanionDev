"""
Domain models for the AI Dev Companion API.

This module contains all Pydantic models used for request/response validation
and serialization throughout the application.
"""

from typing import Any, Dict, Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ChatRequest(BaseModel):
    """
    Request model for code analysis endpoints.
    
    Supports both 'source_code' and legacy 'code_snippet' fields for compatibility.
    Now includes conversation support for multi-turn interactions.
    """
    
    source_code: Optional[str] = Field(
        default=None,
        description="Source code to analyze",
        min_length=1
    )
    code_snippet: Optional[str] = Field(
        default=None,
        description="Source code to analyze (legacy field)",
        min_length=1
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID of existing conversation to continue, or None to start new"
    )
    message: Optional[str] = Field(
        default=None,
        description="User message for conversational interaction (e.g., 'yes, fix it', 'explain the performance issue')"
    )
    apply_improvements: Optional[bool] = Field(
        default=None,
        description="Whether to apply suggested improvements"
    )
    extra: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    
    def get_code(self) -> Optional[str]:
        """
        Get the source code, preferring source_code over code_snippet.
        
        Returns:
            The source code string, or None if neither field is provided
        """
        return self.source_code or self.code_snippet
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "source_code": "fun main() { println(\"Hello\") }",
                "conversation_id": "abc123",
                "message": "Yes, please fix the security issues"
            }
        }
    }


class Issue(BaseModel):
    """
    Represents a single code quality issue found during analysis.
    """
    
    type: Optional[str] = Field(
        default=None,
        description="Issue type (e.g., PERFORMANCE, SECURITY, BEST_PRACTICE)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed description of the issue"
    )
    suggestion: Optional[str] = Field(
        default=None,
        description="Suggested fix or improvement"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "PERFORMANCE",
                "description": "Inefficient loop detected",
                "suggestion": "Use list comprehension instead of append in loop",
            }
        }
    }


class ChatResponse(BaseModel):
    """
    Response model for code analysis endpoints.
    
    Contains a summary of findings, list of specific issues, and conversation context.
    """
    
    summary: Optional[str] = Field(
        default=None,
        description="Overall summary of the code analysis"
    )
    issues: Optional[List[Issue]] = Field(
        default=None,
        description="List of issues found in the code"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID of the conversation for follow-up interactions"
    )
    improved_code: Optional[str] = Field(
        default=None,
        description="Improved version of the code (when user requested fixes)"
    )
    awaiting_user_input: Optional[bool] = Field(
        default=False,
        description="Whether the agent is waiting for user decision/input"
    )
    suggested_actions: Optional[List[str]] = Field(
        default=None,
        description="Suggested next actions for the user"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "summary": "Code analysis completed. Found 2 issues.",
                "issues": [
                    {
                        "type": "PERFORMANCE",
                        "description": "Inefficient loop",
                        "suggestion": "Use list comprehension",
                    }
                ],
            }
        }
    }


class JobSubmitResponse(BaseModel):
    """
    Response model for job submission endpoint.
    """
    
    job_id: str = Field(
        description="Unique identifier for the submitted job"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    }


class JobStatusResponse(BaseModel):
    """
    Response model for job status endpoint.
    """
    
    job_id: str = Field(
        description="Unique identifier for the job"
    )
    status: str = Field(
        description="Current status of the job (queued, running, done, error)"
    )
    created_at: Optional[float] = Field(
        default=None,
        description="Timestamp when the job was created"
    )
    updated_at: Optional[float] = Field(
        default=None,
        description="Timestamp when the job was last updated"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
                "created_at": 1699401234.567,
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Standardized error response model.
    
    This model is used for all error responses to ensure consistency.
    """
    
    error: Dict[str, Any] = Field(
        description="Error details"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "type": "rate_limit_exceeded",
                    "message": "Too many requests. Try again in 42 seconds.",
                    "retry_after": 42,
                }
            }
        }
    }


# ============================================================================
# Conversation Models - For multi-turn stateful interactions
# ============================================================================

class Message(BaseModel):
    """
    Represents a single message in a conversation.
    """
    
    role: Literal["user", "assistant"] = Field(
        description="Who sent the message"
    )
    content: str = Field(
        description="The message content"
    )
    timestamp: float = Field(
        default_factory=lambda: datetime.now().timestamp(),
        description="Unix timestamp when message was created"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional message metadata (e.g., code snippets, issues found)"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "role": "user",
                "content": "Analyze this code",
                "timestamp": 1699401234.567,
                "metadata": {"source_code": "fun main() { }"}
            }
        }
    }


class ConversationState(BaseModel):
    """
    Tracks the current state of a conversation.
    """
    
    original_code: Optional[str] = Field(
        default=None,
        description="The original code submitted for analysis"
    )
    current_code: Optional[str] = Field(
        default=None,
        description="The current version of the code (after any applied fixes)"
    )
    detected_issues: Optional[List[Issue]] = Field(
        default=None,
        description="All issues detected in the original code"
    )
    pending_issues: Optional[List[str]] = Field(
        default=None,
        description="Issue types that haven't been fixed yet"
    )
    applied_fixes: Optional[List[str]] = Field(
        default=None,
        description="Issue types that have been fixed"
    )
    awaiting_decision: Optional[bool] = Field(
        default=False,
        description="Whether we're waiting for user to decide on improvements"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "original_code": "fun main() { }",
                "current_code": "fun main() { }",
                "pending_issues": ["PERFORMANCE", "SECURITY"],
                "applied_fixes": [],
                "awaiting_decision": True
            }
        }
    }


class Conversation(BaseModel):
    """
    Represents a complete conversation session.
    """
    
    conversation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique conversation identifier"
    )
    created_at: float = Field(
        default_factory=lambda: datetime.now().timestamp(),
        description="When conversation was started"
    )
    updated_at: float = Field(
        default_factory=lambda: datetime.now().timestamp(),
        description="Last message timestamp"
    )
    messages: List[Message] = Field(
        default_factory=list,
        description="Conversation message history"
    )
    state: ConversationState = Field(
        default_factory=ConversationState,
        description="Current conversation state"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation_id": "abc123",
                "created_at": 1699401234.567,
                "updated_at": 1699401250.123,
                "messages": [],
                "state": {}
            }
        }
    }


class ConversationListResponse(BaseModel):
    """
    Response model for listing all conversations.
    """
    
    conversations: List[Dict[str, Any]] = Field(
        description="List of conversation summaries"
    )
    total: int = Field(
        description="Total number of conversations"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "conversations": [
                    {
                        "conversation_id": "abc123",
                        "created_at": 1699401234.567,
                        "message_count": 5
                    }
                ],
                "total": 1
            }
        }
    }
