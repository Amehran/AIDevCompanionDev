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
