from fastapi import APIRouter, Query, Depends
from app.core.exceptions import InvalidInput
from app.core.di import get_settings
from app.domain.models import ChatRequest, ChatResponse, Issue

router = APIRouter()

@router.post("/chat")
async def chat(
    body: ChatRequest,
    fast: bool = Query(False, description="Return quick stub response for connectivity testing"),
    debug: bool = Query(False, description="Debug mode: skip OpenAI call and report diagnostics"),
    settings = Depends(get_settings),
):
    code = body.get_code()
    if not code:
        # Allow global AppException handler to produce proper 422
        raise InvalidInput("Provide 'source_code' or 'code_snippet'.")

    if fast:
        return ChatResponse(summary="OK (fast mode)", issues=[])

    if debug:
        # Do not call external APIs; just report import/config status
        import_ok = False
        openai_version = None
        try:
            import openai  # type: ignore
            import_ok = True
            openai_version = getattr(openai, "__version__", "unknown")
        except Exception:
            import_ok = False
        has_key = bool(settings.openai_api_key)
        model_name = settings.model or "gpt-4o-mini"
        return ChatResponse(
            summary=f"debug: import_ok={import_ok}, openai_version={openai_version}, has_key={has_key}, model={model_name}",
            issues=[],
        )

    # If running in test mode (dummy key), return stub to avoid external calls
    if (settings.openai_api_key or "").lower() in {"dummy", "test", "placeholder"}:
        return ChatResponse(summary="OK (test mode)", issues=[])

    # Lightweight OpenAI-based review
    try:
        import openai
        client = openai.OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.model or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a code review assistant. Analyze the code and return a JSON with 'summary' (string) and 'issues' (array of objects with 'type', 'description', 'suggestion')."},
                {"role": "user", "content": f"Review this code:\n\n{code}"}
            ],
            temperature=0.3
        )
        result_text = response.choices[0].message.content
        import json
        try:
            parsed = json.loads(result_text)
            summary = parsed.get("summary", result_text)
            issues_data = parsed.get("issues", [])
            issues = [
                Issue(
                    type=item.get("type"),
                    description=item.get("description"),
                    suggestion=item.get("suggestion")
                )
                for item in issues_data if isinstance(item, dict)
            ]
            return ChatResponse(summary=summary, issues=issues)
        except json.JSONDecodeError:
            return ChatResponse(summary=result_text, issues=[])
    except ImportError as e:
        return ChatResponse(summary=f"OpenAI module not available: {str(e)}", issues=[])
    except Exception as e:
        import traceback
        error_detail = f"Error during OpenAI code review: {str(e)}\nType: {type(e).__name__}\nTrace: {traceback.format_exc()}"
        return ChatResponse(summary=error_detail, issues=[])

