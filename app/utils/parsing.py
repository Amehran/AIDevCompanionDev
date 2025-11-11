"""Shared LLM response parsing logic.

Extracts JSON from LLM crew/OpenAI output and converts to ChatResponse model.
"""
import json
from app.domain.models import ChatResponse, Issue


def parse_llm_json(text: str) -> ChatResponse:
    """Parse LLM output (expected JSON) into ChatResponse.
    
    Falls back to raw text in summary if parsing fails.
    """
    try:
        data = json.loads(text)
        summary = data.get("summary") if isinstance(data, dict) else None
        raw_issues = data.get("issues") if isinstance(data, dict) else []
        issues: list[Issue] = []
        if isinstance(raw_issues, list):
            for item in raw_issues:
                if isinstance(item, dict):
                    issues.append(
                        Issue(
                            type=item.get("type"),
                            description=item.get("description"),
                            suggestion=item.get("suggestion"),
                        )
                    )
        return ChatResponse(summary=summary or text, issues=issues)
    except json.JSONDecodeError:
        return ChatResponse(summary=text, issues=[])
