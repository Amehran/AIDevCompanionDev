from fastapi import APIRouter

router = APIRouter()

@router.get("/diag")
async def diag():
    import os
    info = {
        "commit": os.getenv("APP_COMMIT_SHA"),
        "model": os.getenv("MODEL"),
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "aws_env": os.getenv("AWS_EXECUTION_ENV"),
    }
    # Check openai import without failing
    try:
        import openai  # type: ignore
        info["openai_import"] = True
        info["openai_version"] = getattr(openai, "__version__", "unknown")
    except Exception as e:
        info["openai_import"] = False
        info["openai_import_error"] = str(e)
    return info
