"""Custom DRF exception handler — converts all exceptions to structured responses."""
from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .api_exceptions import TenderExtractorBaseException, ValidationException
from .error_codes import ErrorCode

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """DRF custom exception handler."""

    # Handle our own domain exceptions first
    if isinstance(exc, TenderExtractorBaseException):
        logger.warning(
            "Domain exception",
            extra={
                "response_code": int(exc.response_code),
                "detail": exc.message,
                "exc_type": type(exc).__name__,
            },
        )
        return Response(exc.to_dict(), status=exc.http_status)

    # Fall through to DRF default handler (handles 404, 405, etc.)
    response = exception_handler(exc, context)

    if response is not None:
        # Normalise DRF error responses to our format
        detail = response.data.get("detail", str(exc))
        code = _map_status_to_error_code(response.status_code)
        response.data = {
            "response_code": int(code),
            "message": str(detail),
        }
        return response

    # Unexpected exception — log and return 500 without exposing internals
    logger.exception("Unhandled exception", exc_info=exc)
    return Response(
        {
            "response_code": int(ErrorCode.INTERNAL_SERVER_ERROR),
            "message": "An internal server error occurred.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _map_status_to_error_code(http_status: int) -> ErrorCode:
    mapping = {
        401: ErrorCode.AUTHENTICATION_FAILED,
        403: ErrorCode.PERMISSION_DENIED,
        400: ErrorCode.MISSING_REQUEST_ID,
    }
    return mapping.get(http_status, ErrorCode.INTERNAL_SERVER_ERROR)
