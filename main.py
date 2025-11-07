from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Any, Dict, Optional
import sys
import logging

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
    logger.info(f"Incoming {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(
        f"Completed {request.method} {request.url.path} -> {response.status_code}"
    )
    return response


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
async def chat(body: ChatRequest):
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
        logger.info(f"Building crew for code: {code[:50]}...")
        # Build the Crew and run with given inputs
        project = CodeReviewProject()
        crew = project.code_review_crew()
        logger.info("Crew built, starting kickoff...")
        raw_result = crew.kickoff(inputs={"source_code": code})
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
        import traceback

        logger.error(f"ERROR in /chat: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
