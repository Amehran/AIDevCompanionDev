"""OpenAI-powered code analysis endpoint.

POST /chat/analyze
Body: ChatRequest (source_code or code_snippet)
Response: ChatResponse with summary + issues parsed from model output.
Falls back gracefully on errors and never raises unhandled exceptions.
"""
from fastapi import APIRouter
from app.domain.models import ChatRequest, ChatResponse, Issue
from app.core.exceptions import InvalidInput
from app.core.config import settings
import json
import traceback

router = APIRouter()

_SYSTEM_PROMPT = (
    "You are an expert mobile code review assistant. Given source code, output ONLY a JSON "
    "object with keys 'summary' and 'issues'. 'issues' is a list of objects with 'type', "
    "'description', and 'suggestion'. If no issues, return an empty list."
)

_DEF_MODEL = "gpt-4o-mini"


def _model_name() -> str:
    return settings.effective_model if getattr(settings, "effective_model", None) else _DEF_MODEL


def _parse_llm_json(text: str) -> ChatResponse:
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
        # Return raw text if not valid JSON
        return ChatResponse(summary=text, issues=[])


@router.post("/chat/analyze")
async def chat_analyze(body: ChatRequest):
    code = body.get_code()
    if not code:
        raise InvalidInput("Provide 'source_code' or 'code_snippet'.")

    # If no real key, do deterministic stub so client still works.
    key = (settings.openai_api_key or "").strip()
    if not key or key.lower() in {"dummy", "test", "placeholder"}:
        preview = code[:80].replace("\n", " ")
        return ChatResponse(summary=f"Stub LLM review (no key) | preview: {preview}", issues=[])

    try:
        import openai  # type: ignore
        client = openai.OpenAI(api_key=key)
        response = client.chat.completions.create(
            model=_model_name(),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": code},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return _parse_llm_json(content)
    except ImportError as e:
        return ChatResponse(summary=f"openai_import_error: {e}", issues=[])
    except Exception as e:
        detail = {
            "message": str(e),
            "type": type(e).__name__,
            "trace": traceback.format_exc(),
        }
        return ChatResponse(summary=f"openai_runtime_error: {detail}", issues=[])
