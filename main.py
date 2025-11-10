from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict, Optional
import sys
import logging
import os

from src.crew import CodeReviewProject  # type: ignore
from app.core.config import Settings, get_settings, settings
from app.core.di import rate_limiter, job_manager
from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.jobs import router as jobs_router
from app.core.error_handlers import register_exception_handlers
# Structured exceptions available for future use
# Placeholder: structured exceptions available for future integration
# (Removed unused imports to satisfy lint.)
from app.domain.models import (
    ChatRequest,
    ChatResponse,
    Issue,
)

# Force unbuffered output
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)
logger = logging.getLogger(__name__)

# Load .env only in local dev (Lambda gets env vars from function config)
if os.getenv("AWS_EXECUTION_ENV") is None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed; fine in Lambda

app = FastAPI()
# Initialize services (use DI singletons)

# Expose internal state for tests (back-compat with tests/test_api.py)
_rate_lock = rate_limiter._lock  # type: ignore[attr-defined]
_rate_buckets = rate_limiter.buckets
_jobs_lock = job_manager._lock  # type: ignore[attr-defined]
_jobs = job_manager.jobs


# Lightweight logging (avoid consuming body so external POST works)
@app.middleware("http")
async def basic_logging(request, call_next):
    try:
        logger.info(
            f"Incoming {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}"
        )
        response = await call_next(request)
        logger.info(
            f"Completed {request.method} {request.url.path} -> {response.status_code}"
        )
        return response
    except Exception as e:
        logger.error(f"Middleware error for {request.method} {request.url.path}: {e}")
        import traceback

        logger.error(traceback.format_exc())
        raise

register_exception_handlers(app)

# Include routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(jobs_router)


@app.get("/")
async def root():
    return {"message": "Hello from ai-dev-companion-backend!"}


@app.post("/test")
async def test_post():
    print("=== TEST POST received ===", flush=True)
    return {"status": "ok"}


@app.post("/echo")
async def echo(payload: Dict[str, Any]):
    """Debug endpoint: returns payload verbatim to help client integration."""
    return {"received": payload}


@app.post("/chat")
async def chat(
    body: ChatRequest,
    fast: bool = Query(
        False, description="Return quick stub response for connectivity testing"
    ),
    settings: Settings = Depends(get_settings),
):
    logger.info("=== POST /chat received ===")
    logger.info(f"Request body: {body}")
    code = body.get_code()
    if not code:
        logger.error("No code provided in request")
        raise HTTPException(
            status_code=422, detail="Provide 'source_code' or 'code_snippet'."
        )

    try:
        # Fast path to verify clients without invoking LLM
        if fast:
            logger.info("Fast=true -> returning stub response")
            return ChatResponse(summary="OK (fast mode)", issues=[])

        logger.info(f"Building crew for code: {code[:50]}...")
        # Build the Crew and run with given inputs
        project = CodeReviewProject()
        crew = project.code_review_crew()
        logger.info("Crew built, starting kickoff...")
        # Run blocking LLM call in a worker thread so event loop stays responsive
        raw_result = await run_in_threadpool(
            lambda: crew.kickoff(inputs={"source_code": code})
        )
        logger.info("Kickoff complete!")

        # raw_result may already be JSON string; attempt to parse
        import json

        parsed = None
        try:
            parsed = json.loads(str(raw_result))
        except Exception:
            logger.warning("Result not valid JSON, wrapping as summary text")
            return ChatResponse(summary=str(raw_result), issues=[])

        # Normalize structure
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
        # Structured error response
        import traceback

        logger.error(f"ERROR in /chat: {str(e)}")
        trace = traceback.format_exc()
        logger.error(trace)
        payload = {
            "error": {
                "type": "internal_error",
                "message": "An unexpected error occurred while analyzing the code.",
                "details": str(e),
            }
        }
        return JSONResponse(status_code=500, content=payload)


# =========================
# Async (job-based) variant
# =========================

JobRecord = Dict[str, Any]


def _get_job(job_id: str) -> Optional[JobRecord]:
    return job_manager.get(job_id)


def _cleanup_jobs(ttl_seconds: int = 3600) -> int:
    return job_manager.cleanup(ttl_seconds)


async def _analyze_code_to_response(code: str) -> ChatResponse:
    logger.info(f"[job] Analyzing code len={len(code)}")
    # Test-mode shortcut: when using a dummy/test API key, avoid real LLM calls
    if (settings.openai_api_key or "").lower() in {"dummy", "test", "placeholder"}:
        return ChatResponse(summary="OK (test mode)", issues=[])
    project = CodeReviewProject()
    crew = project.code_review_crew()
    raw_result = await run_in_threadpool(
        lambda: crew.kickoff(inputs={"source_code": code})
    )
    import json

    try:
        parsed = json.loads(str(raw_result))
    except Exception:
        return ChatResponse(summary=str(raw_result), issues=[])

    summary = parsed.get("summary") if isinstance(parsed, dict) else None
    issues: list[Issue] = []
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


# =========================
# Rate limiting helpers
# =========================


def _rate_limit_check(ip: str) -> Optional[int]:
    """Return retry_after seconds if limited, else None."""
    return rate_limiter.check(ip)


def _active_jobs_count() -> int:
    return job_manager.active_count()


@app.post("/chat/submit")
async def submit_chat(
    request: Request, body: ChatRequest, settings: Settings = Depends(get_settings)
) -> Dict[str, str]:
    # Per-IP rate limiting (fixed 60s window)
    ip = request.client.host if request.client else "unknown"
    retry_after = _rate_limit_check(ip)
    if retry_after is not None:
        payload = {
            "error": {
                "type": "rate_limit_exceeded",
                "message": f"Too many requests. Try again in {retry_after} seconds.",
                "retry_after": retry_after,
            }
        }
        return JSONResponse(
            status_code=429, headers={"Retry-After": str(retry_after)}, content=payload
        )

    # Global concurrent jobs guard
    active = _active_jobs_count()
    if active >= settings.max_concurrent_jobs:
        payload = {
            "error": {
                "type": "server_busy",
                "message": "Server is busy. Please try again shortly.",
                "details": {
                    "active_jobs": active,
                    "max_concurrent": settings.max_concurrent_jobs,
                },
            }
        }
        return JSONResponse(status_code=503, content=payload)

    code = body.source_code or body.code_snippet
    if not code:
        raise HTTPException(
            status_code=422, detail="Provide 'source_code' or 'code_snippet'."
        )

    job_id = job_manager.create_job()

    async def job_coro():
        return await _analyze_code_to_response(code)

    import asyncio
    asyncio.create_task(job_manager.run_job(job_id, job_coro))

    return {"job_id": job_id}


@app.get("/chat/status/{job_id}")
async def chat_status(job_id: str) -> Dict[str, Any]:
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "created_at": job.get("created_at"),
    }


@app.get("/chat/result/{job_id}")
async def chat_result(job_id: str):
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    status = job.get("status")
    if status == "done":
        return JSONResponse(content=job.get("result") or {})
    if status == "error":
        raise HTTPException(status_code=500, detail=job.get("error") or "unknown error")
    return JSONResponse(status_code=202, content={"job_id": job_id, "status": status})


@app.delete("/chat/jobs/cleanup")
async def chat_jobs_cleanup(ttl: int = Query(3600, ge=60, le=86400)) -> Dict[str, int]:
    removed = _cleanup_jobs(ttl)
    return {"removed": removed}
