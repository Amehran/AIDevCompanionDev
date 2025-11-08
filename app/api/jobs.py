from fastapi import APIRouter, HTTPException, Query, Request, Depends
from app.core.exceptions import RateLimitExceeded, ServerBusy, InvalidInput, JobNotFound
from fastapi.responses import JSONResponse
import asyncio
from typing import Dict, Any

from app.core.di import get_settings, get_rate_limiter, get_job_manager
from app.domain.models import ChatRequest, ChatResponse
from app.core.di import settings
from src.crew import CodeReviewProject  # type: ignore
from starlette.concurrency import run_in_threadpool

router = APIRouter()

async def _analyze_code(code: str) -> ChatResponse:
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
        from app.domain.models import Issue
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

@router.post("/chat/submit")
async def submit_chat(
    request: Request,
    body: ChatRequest,
    settings = Depends(get_settings),
    rate_limiter = Depends(get_rate_limiter),
    job_manager = Depends(get_job_manager),
) -> Dict[str, str]:
    ip = request.client.host if request.client else "unknown"
    retry_after = rate_limiter.check(ip)
    if retry_after is not None:
        raise RateLimitExceeded(retry_after)

    active = job_manager.active_count()
    if active >= settings.max_concurrent_jobs:
        raise ServerBusy(active_jobs=active, max_concurrent=settings.max_concurrent_jobs)

    code = body.get_code()
    if not code:
        raise InvalidInput("Provide 'source_code' or 'code_snippet'.")

    job_id = job_manager.create_job()

    async def job_coro():
        return await _analyze_code(code)

    asyncio.create_task(job_manager.run_job(job_id, job_coro))
    return {"job_id": job_id}

@router.get("/chat/status/{job_id}")
async def chat_status(job_id: str, job_manager = Depends(get_job_manager)) -> Dict[str, Any]:
    job = job_manager.get(job_id)
    if not job:
        raise JobNotFound(job_id)
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "created_at": job.get("created_at"),
    }

@router.get("/chat/result/{job_id}")
async def chat_result(job_id: str, job_manager = Depends(get_job_manager)):
    job = job_manager.get(job_id)
    if not job:
        raise JobNotFound(job_id)
    status = job.get("status")
    if status == "done":
        return JSONResponse(content=job.get("result") or {})
    if status == "error":
        raise HTTPException(status_code=500, detail=job.get("error") or "unknown error")
    return JSONResponse(status_code=202, content={"job_id": job_id, "status": status})

@router.delete("/chat/jobs/cleanup")
async def chat_jobs_cleanup(ttl: int = Query(3600, ge=60, le=86400), job_manager = Depends(get_job_manager)) -> Dict[str, int]:
    removed = job_manager.cleanup(ttl)
    return {"removed": removed}
