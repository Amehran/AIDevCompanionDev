"""Diagnostics endpoint.

Returns deployment + runtime metadata to verify that the correct Lambda
function/version is serving traffic. Designed to be resilient: any internal
error produces a JSON payload instead of a 500 so we can always see *something*.
"""

from fastapi import APIRouter
import os

router = APIRouter()


@router.get("/diag")
async def diag():  # pragma: no cover - simple metadata endpoint
    payload = {
        "commit": os.getenv("APP_COMMIT_SHA"),
        "model_env": os.getenv("MODEL"),
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "aws_execution_env": os.getenv("AWS_EXECUTION_ENV"),
        "python_version": os.getenv("PYTHON_VERSION") or os.getenv("AWS_EXECUTION_ENV"),
    }

    # Attempt to surface configured pydantic settings (if they loaded successfully)
    try:
        from app.core.config import settings  # type: ignore
        payload["settings_effective_model"] = settings.effective_model
        payload["settings_openai_key_present"] = bool(settings.openai_api_key)
    except Exception as e:  # settings may fail validation if key missing
        payload["settings_error"] = str(e)

    # Enumerate registered routes to ensure the expected router is active
    try:
        from main import app  # local import to avoid circular issues at module import time
        route_paths = []
        for r in app.routes:
            try:
                route_paths.append(getattr(r, "path", "<unknown>"))
            except Exception:
                continue
        payload["routes"] = sorted(route_paths)
    except Exception as e:
        payload["routes_error"] = str(e)

    # Check openai import status without failing
    try:
        import openai  # type: ignore
        payload["openai_import"] = True
        payload["openai_version"] = getattr(openai, "__version__", "unknown")
    except Exception as e:
        payload["openai_import"] = False
        payload["openai_import_error"] = str(e)

    return payload
