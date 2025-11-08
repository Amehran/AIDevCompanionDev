from fastapi import APIRouter
from typing import Any, Dict

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Hello from ai-dev-companion-backend!"}

@router.post("/test")
async def test_post():
    return {"status": "ok"}

@router.post("/echo")
async def echo(payload: Dict[str, Any]):
    return {"received": payload}
