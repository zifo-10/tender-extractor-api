"""Custom exception classes for the Tender Extractor API."""
from __future__ import annotations

from typing import Optional

from .error_codes import ErrorCode


class TenderExtractorBaseException(Exception):
    """Base exception class.  All domain exceptions inherit from this."""

    response_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR
    default_message: str = "An unexpected error occurred."
    http_status: int = 500

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        response_code: Optional[ErrorCode] = None,
        http_status: Optional[int] = None,
    ) -> None:
        self.message = message or self.default_message
        if response_code is not None:
            self.response_code = response_code
        if http_status is not None:
            self.http_status = http_status
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "response_code": int(self.response_code),
            "message": self.message,
        }


class ValidationException(TenderExtractorBaseException):
    """Raised when request validation fails."""

    response_code = ErrorCode.MISSING_REQUEST_ID
    default_message = "Validation error."
    http_status = 400

    def __init__(
        self,
        message: str,
        response_code: ErrorCode,
        http_status: int = 400,
    ) -> None:
        super().__init__(message, response_code=response_code, http_status=http_status)


class MissingFieldException(ValidationException):
    """Raised when a required field is absent."""

    def __init__(self, field_name: str) -> None:
        code_map = {
            "request_id": ErrorCode.MISSING_REQUEST_ID,
            "text": ErrorCode.MISSING_TEXT,
        }
        code = code_map.get(field_name, ErrorCode.MISSING_REQUEST_ID)
        super().__init__(
            message=f"{field_name} field is required",
            response_code=code,
        )


class InvalidFieldValueException(ValidationException):
    """Raised when a field value is invalid."""

    def __init__(self, field_name: str, message: str) -> None:
        code_map = {
            "output_language": ErrorCode.INVALID_OUTPUT_LANGUAGE,
            "text": ErrorCode.TEXT_TOO_SHORT,
        }
        code = code_map.get(field_name, ErrorCode.MISSING_REQUEST_ID)
        super().__init__(message=message, response_code=code)


class LLMProviderException(TenderExtractorBaseException):
    """Raised when a single LLM provider call fails."""

    response_code = ErrorCode.LLM_PROVIDER_ERROR
    default_message = "LLM provider error."
    http_status = 500

    def __init__(self, provider: str, reason: str) -> None:
        self.provider = provider
        super().__init__(
            message=f"Provider '{provider}' failed: {reason}",
            response_code=ErrorCode.LLM_PROVIDER_ERROR,
        )


class AllProvidersFailedException(TenderExtractorBaseException):
    """Raised when all LLM providers fail — handled gracefully at the API layer."""

    response_code = ErrorCode.ALL_PROVIDERS_FAILED
    default_message = "All LLM providers failed."
    http_status = 200  # graceful — return default payload


class AuthenticationException(TenderExtractorBaseException):
    """Raised for authentication / authorisation failures."""

    response_code = ErrorCode.AUTHENTICATION_FAILED
    default_message = "Authentication failed."
    http_status = 401
