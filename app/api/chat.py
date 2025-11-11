"""Unified /chat endpoint with optional OpenAI analysis.

Query params:
- mode: "stub" (default, fast) or "full" (OpenAI analysis)

Examples:
- POST /chat → stub (instant)
- POST /chat?mode=full → OpenAI analysis (2-5s)
"""

from fastapi import APIRouter, Query
from app.core.exceptions import InvalidInput
from app.domain.models import ChatRequest, ChatResponse
from app.core.config import settings
from app.utils.parsing import parse_llm_json
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


@router.post("/chat")
async def chat(
    body: ChatRequest,
    mode: str = Query("stub", description="Analysis mode: 'stub' (fast) or 'full' (OpenAI)")
):
    code = body.get_code()
    if not code:
        raise InvalidInput("Provide 'source_code' or 'code_snippet'.")

    # Stub mode (default): instant response
    if mode != "full":
        preview = code[:80].replace("\n", " ")
        return ChatResponse(summary=f"Stub review OK | preview: {preview}", issues=[])

    # Full mode: OpenAI analysis
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
        return parse_llm_json(content)
    except ImportError as e:
        return ChatResponse(summary=f"openai_import_error: {e}", issues=[])
    except Exception as e:
        detail = {
            "message": str(e),
            "type": type(e).__name__,
            "trace": traceback.format_exc(),
        }
        return ChatResponse(summary=f"openai_runtime_error: {detail}", issues=[])

