from fastapi import APIRouter, Query, Depends
from app.core.exceptions import InvalidInput
from starlette.concurrency import run_in_threadpool
from app.core.di import get_settings
from app.domain.models import ChatRequest, ChatResponse, Issue
from src.crew import CodeReviewProject  # type: ignore

router = APIRouter()

@router.post("/chat")
async def chat(
    body: ChatRequest,
    fast: bool = Query(False, description="Return quick stub response for connectivity testing"),
    settings = Depends(get_settings),
):
    code = body.get_code()
    if not code:
        raise InvalidInput("Provide 'source_code' or 'code_snippet'.")

    if fast:
        return ChatResponse(summary="OK (fast mode)", issues=[])

    # If running in test mode (dummy key), return stub to avoid external calls
    if (settings.openai_api_key or "").lower() in {"dummy", "test", "placeholder"}:
        return ChatResponse(summary="OK (test mode)", issues=[])

    # Lightweight OpenAI-based review (without CrewAI) for Lambda deployment
    # TODO: Implement Lambda Layer or Container Image for full CrewAI support
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
    except ImportError:
        # OpenAI not available, try CrewAI fallback
        pass
    except Exception as e:
        return ChatResponse(summary=f"Error during code review: {str(e)}", issues=[])

    # Fallback to CrewAI if OpenAI import failed (for local dev or container deployment)
    try:
        project = CodeReviewProject()
        crew = project.code_review_crew()
        raw_result = await run_in_threadpool(lambda: crew.kickoff(inputs={"source_code": code}))

        import json
        try:
            parsed = json.loads(str(raw_result))
        except Exception:
            return ChatResponse(summary=str(raw_result), issues=[])

        summary = parsed.get("summary") if isinstance(parsed, dict) else None
        issues = []
        if isinstance(parsed, dict) and isinstance(parsed.get("issues"), list):
            for item in parsed["issues"]:
                if isinstance(item, dict):
                    issues.append(
                        Issue(
                            type=item.get("type"),
                            description=item.get("description"),
                            suggestion=item.get("suggestion"),
                        )
                    )
        return ChatResponse(summary=summary, issues=issues)
    except Exception as e:
        return ChatResponse(summary=f"CrewAI fallback error: {str(e)}", issues=[])
