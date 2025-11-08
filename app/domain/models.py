"""
Domain models for the AI Dev Companion API.

This module contains all Pydantic models used for request/response validation
and serialization throughout the application.
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request model for code analysis endpoints.
    
    Supports both 'source_code' and legacy 'code_snippet' fields for compatibility.
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
                "source_code": "fun main() { println(\"Hello\") }"
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
    
    Contains a summary of findings and a list of specific issues.
    """
    
    summary: Optional[str] = Field(
        default=None,
        description="Overall summary of the code analysis"
    )
    issues: Optional[List[Issue]] = Field(
        default=None,
        description="List of issues found in the code"
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
