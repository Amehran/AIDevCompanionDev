from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from app.core.error_handlers import (
    app_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)
from app.core.exceptions import InvalidInput, RateLimitExceeded
import pytest
from pydantic import ValidationError

class TestErrorHandlers:
    def test_app_exception_handler(self):
        """Should format AppException correctly."""
        exc = InvalidInput("Invalid data")
        response = app_exception_handler(Request({"type": "http"}), exc)
        
        assert response.status_code == 400
        data =  import_json().loads(response.body)
        assert data["error"]["type"] == "InvalidInput"
        assert data["error"]["message"] == "Invalid data"
        assert data["detail"] == "Invalid data"  # Back-compat

    def test_rate_limit_handler(self):
        """Should format RateLimitExceeded correctly."""
        exc = RateLimitExceeded(retry_after=30)
        response = app_exception_handler(Request({"type": "http"}), exc)
        
        assert response.status_code == 429
        data = import_json().loads(response.body)
        assert data["error"]["type"] == "RateLimitExceeded"
        assert data["retry_after"] == 30

    def test_validation_exception_handler(self):
        """Should format RequestValidationError correctly."""
        # Create a mock validation error
        exc = RequestValidationError(
            [{"loc": ("body", "field"), "msg": "field required", "type": "value_error.missing"}]
        )
        response = validation_exception_handler(Request({"type": "http"}), exc)
        
        assert response.status_code == 422
        data = import_json().loads(response.body)
        assert data["error"]["type"] == "invalid_input"
        assert data["error"]["message"] == "Validation failed."
        assert len(data["error"]["details"]) == 1
        assert data["error"]["details"][0]["msg"] == "field required"

    def test_unhandled_exception_handler(self):
        """Should format generic Exception correctly."""
        exc = Exception("Boom!")
        response = unhandled_exception_handler(Request({"type": "http"}), exc)
        
        assert response.status_code == 500
        data = import_json().loads(response.body)
        assert data["error"]["type"] == "internal_error"
        assert data["error"]["message"] == "An unexpected error occurred."
        # Should not leak exception details
        assert "Boom!" not in str(data)

def import_json():
    import json
    return json
