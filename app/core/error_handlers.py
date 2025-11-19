"""Global exception handlers registration."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import AppException


def app_exception_handler(request: Request, exc: AppException):
    data = exc.to_dict()
    # Back-compat for clients/tests expecting 'detail'
    if "error" in data and "message" in data["error"]:
        data.setdefault("detail", data["error"]["message"])
    return JSONResponse(status_code=exc.status_code, content=data)


def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Mirror InvalidInput style but keep FastAPI validation detail
    details = []
    for err in exc.errors():
        details.append({
            "loc": err.get("loc"),
            "msg": err.get("msg"),
            "type": err.get("type"),
        })
    payload = {
        "error": {
            "type": "invalid_input",
            "message": "Validation failed.",
            "details": details,
        }
    }
    return JSONResponse(status_code=422, content=payload)


def unhandled_exception_handler(request: Request, exc: Exception):
    payload = {
        "error": {
            "type": "internal_error",
            "message": "An unexpected error occurred.",
        }
    }
    return JSONResponse(status_code=500, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
