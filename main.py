from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
import uuid
import time
import threading
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Any, Dict, Optional
import sys
import logging
import os

from src.crew import CodeReviewProject  # type: ignore

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

load_dotenv()

app = FastAPI()


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


@app.get("/")
async def root():
    return {"message": "Hello from ai-dev-companion-backend!"}


@app.post("/test")
async def test_post():
    print("=== TEST POST received ===", flush=True)
    return {"status": "ok"}


class ChatRequest(BaseModel):
    # Accept either field for compatibility
    source_code: Optional[str] = None
    code_snippet: Optional[str] = None
    # Add optional fields as needed in the future
    extra: Optional[Dict[str, Any]] = None


class Issue(BaseModel):
    type: Optional[str]
    description: Optional[str]
    suggestion: Optional[str]


class ChatResponse(BaseModel):
    summary: Optional[str]
    issues: Optional[list[Issue]]


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
):
    logger.info("=== POST /chat received ===")
    logger.info(f"Request body: {body}")
    logger.info(f"source_code: {body.source_code}")
    logger.info(f"code_snippet: {body.code_snippet}")
    # Support both 'source_code' and legacy 'code_snippet'
    code = body.source_code or body.code_snippet
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
_jobs: Dict[str, JobRecord] = {}
_jobs_lock = threading.Lock()


def _store_job(job_id: str, record: JobRecord) -> None:
    with _jobs_lock:
        _jobs[job_id] = record


def _get_job(job_id: str) -> Optional[JobRecord]:
    with _jobs_lock:
        return _jobs.get(job_id)


def _cleanup_jobs(ttl_seconds: int = 3600) -> int:
    now = time.time()
    removed = 0
    with _jobs_lock:
        stale = [
            jid
            for jid, rec in _jobs.items()
            if now - rec.get("created_at", now) > ttl_seconds
        ]
        for jid in stale:
            _jobs.pop(jid, None)
            removed += 1
    return removed


async def _analyze_code_to_response(code: str) -> ChatResponse:
    logger.info(f"[job] Analyzing code len={len(code)}")
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

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "100"))

_rate_lock = threading.Lock()
_rate_buckets: Dict[str, Dict[str, Any]] = {}


def _rate_limit_check(ip: str) -> Optional[int]:
    """Return retry_after seconds if limited, else None."""
    now = time.time()
    window = 60.0
    with _rate_lock:
        b = _rate_buckets.get(ip)
        if not b:
            _rate_buckets[ip] = {"count": 1, "reset": now + window}
            return None
        if now > b["reset"]:
            b["count"], b["reset"] = 1, now + window
            return None
        if b["count"] >= RATE_LIMIT_PER_MINUTE:
            return max(1, int(b["reset"] - now))
        b["count"] += 1
        return None


def _active_jobs_count() -> int:
    with _jobs_lock:
        return sum(
            1 for j in _jobs.values() if j.get("status") in {"queued", "running"}
        )


@app.post("/chat/submit")
async def submit_chat(request: Request, body: ChatRequest) -> Dict[str, str]:
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
    if active >= MAX_CONCURRENT_JOBS:
        payload = {
            "error": {
                "type": "server_busy",
                "message": "Server is busy. Please try again shortly.",
                "details": {
                    "active_jobs": active,
                    "max_concurrent": MAX_CONCURRENT_JOBS,
                },
            }
        }
        return JSONResponse(status_code=503, content=payload)

    code = body.source_code or body.code_snippet
    if not code:
        raise HTTPException(
            status_code=422, detail="Provide 'source_code' or 'code_snippet'."
        )

    job_id = str(uuid.uuid4())
    _store_job(job_id, {"status": "queued", "created_at": time.time()})

    async def runner():
        _store_job(job_id, {"status": "running", "created_at": time.time()})
        try:
            resp: ChatResponse = await _analyze_code_to_response(code)
            _store_job(
                job_id,
                {
                    "status": "done",
                    "result": resp.model_dump(),
                    "created_at": time.time(),
                },
            )
        except Exception as e:  # pragma: no cover (best-effort logging)
            logger.exception("Job failed: %s", e)
            _store_job(
                job_id, {"status": "error", "error": str(e), "created_at": time.time()}
            )

    # fire-and-forget task
    import asyncio

    asyncio.create_task(runner())

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
