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
    try:
        code = body.get_code()
        if not code:
            raise InvalidInput("Provide 'source_code' or 'code_snippet'.")

        if fast:
            return ChatResponse(summary="OK (fast mode)", issues=[])

        if debug:
            # Diagnostics without external calls
            diag = {
                "import_openai": False,
                "openai_version": None,
                "has_key": bool(settings.openai_api_key),
                "model": settings.model or "gpt-4o-mini",
            }
            try:
                import openai  # type: ignore
                diag["import_openai"] = True
                diag["openai_version"] = getattr(openai, "__version__", "unknown")
            except Exception as imp_err:
                diag["import_error"] = str(imp_err)
            return ChatResponse(summary=f"debug: {diag}", issues=[])

        if (settings.openai_api_key or "").lower() in {"dummy", "test", "placeholder"}:
            return ChatResponse(summary="OK (test mode)", issues=[])

        try:
            import openai
            client = openai.OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.model or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a code review assistant. Analyze the code and return a JSON with 'summary' and 'issues' (list of objects with 'type','description','suggestion'). Return ONLY JSON."},
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
            error_detail = {
                "message": str(e),
                "type": type(e).__name__,
                "trace": traceback.format_exc(),
            }
            return ChatResponse(summary=f"openai_error: {error_detail}", issues=[])
    except InvalidInput:
        # Let global handler produce 422
        raise
    except Exception as e:
        import traceback
        detail = {
            "message": str(e),
            "type": type(e).__name__,
            "trace": traceback.format_exc(),
            "phase": "top_level",
        }
        return ChatResponse(summary=f"unexpected_error: {detail}", issues=[])

