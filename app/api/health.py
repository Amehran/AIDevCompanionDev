from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check():
    """Health check endpoint"""
    key = settings.bedrock_api_key or ""
    return {
        "status": "healthy",
        "service": "ai-dev-companion-backend",
        "api_key_configured": bool(key)
    }
