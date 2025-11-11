from fastapi import APIRouter, Depends
from app.core.di import get_settings

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check(settings = Depends(get_settings)):
    import os
    # Show first 7 chars of API key for debugging (safe to expose prefix)
    key = settings.openai_api_key or ""
    key_preview = key[:7] + "..." if len(key) > 7 else key
    return {
        "status": "ok",
        "openai_key_set": bool(key and key not in ["dummy", "test", "placeholder"]),
        "openai_key_preview": key_preview,
        "aws_env": os.getenv("AWS_EXECUTION_ENV", "not_lambda")
    }
