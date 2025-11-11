"""Diagnostics endpoint (minimal and fully guarded).

Intentionally avoids importing application modules to eliminate circular-import
or initialization side-effects. Always returns JSON; never 500s.
"""

from fastapi import APIRouter
import os

router = APIRouter()


@router.get("/diag")
async def diag():  # pragma: no cover
    try:
        payload = {
            "commit": os.getenv("APP_COMMIT_SHA"),
            "model_env": os.getenv("MODEL"),
            "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
            "aws_execution_env": os.getenv("AWS_EXECUTION_ENV"),
        }

        # Optional: openai import check (fully guarded)
        try:
            import openai  # type: ignore
            payload["openai_import"] = True
            payload["openai_version"] = getattr(openai, "__version__", "unknown")
        except Exception as e:
            payload["openai_import"] = False
            payload["openai_import_error"] = str(e)

        return payload
    except Exception as e:
        # Ultimate guard: never throw from diagnostics
        return {"error": "diag_failed", "message": str(e)}
