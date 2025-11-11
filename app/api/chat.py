"""Minimal /chat endpoint for Android client.

Removes debug/fast/OpenAI logic. Always returns a stub analysis with deterministic
summary and empty issues to keep payload small and predictable.
"""

from fastapi import APIRouter
from app.core.exceptions import InvalidInput
from app.domain.models import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat")
async def chat(body: ChatRequest):
    code = body.get_code()
    if not code:
        raise InvalidInput("Provide 'source_code' or 'code_snippet'.")
    # Deterministic stub summary; truncate code for brevity
    preview = code[:80].replace("\n", " ")
    return ChatResponse(summary=f"Stub review OK | preview: {preview}", issues=[])

