"""Utility helpers for building consistent API responses."""
from __future__ import annotations

from typing import Any


def success_response(data: dict[str, Any]) -> dict[str, Any]:
    """Wrap data in a standard success envelope (pass-through for now)."""
    return data


def error_response(response_code: int, message: str) -> dict[str, Any]:
    """Build a structured error response payload."""
    return {
        "response_code": response_code,
        "message": message,
    }
