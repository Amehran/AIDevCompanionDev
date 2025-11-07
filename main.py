from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Any, Dict, Optional

from src.crew import CodeReviewProject  # type: ignore

load_dotenv()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from ai-dev-companion-backend!"}


class ChatRequest(BaseModel):
    # Accept either field for compatibility
    source_code: Optional[str] = None
    code_snippet: Optional[str] = None
    # Add optional fields as needed in the future
    extra: Optional[Dict[str, Any]] = None


@app.post("/chat")
async def chat(body: ChatRequest):
    # Support both 'source_code' and legacy 'code_snippet'
    code = body.source_code or body.code_snippet
    if not code:
        raise HTTPException(status_code=422, detail="Provide 'source_code' or 'code_snippet'.")

    try:
        # Build the Crew and run with given inputs
        project = CodeReviewProject()
        crew = project.code_review_crew()
        result = crew.kickoff(inputs={"source_code": code})

        # CrewAI may return complex objects; coerce to string for now
        return {"result": str(result)}
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))