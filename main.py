from fastapi import FastAPI
from typing import Any, Dict
import sys
import logging
import os

from app.core.di import rate_limiter, job_manager
from app.api.health import router as health_router
from app.api.diag import router as diag_router
from app.api.chat import router as chat_router
from app.api.jobs import router as jobs_router
from app.core.error_handlers import register_exception_handlers

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
app.include_router(diag_router)


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


# Note: The /chat endpoint is provided by app.api.chat router. We intentionally
# avoid defining a duplicate handler here to prevent routing conflicts.


# (Job endpoints including cleanup are provided by app.api.jobs router; duplicates removed.)
