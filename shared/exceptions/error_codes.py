"""Centralised error codes for validation and application errors."""
from enum import IntEnum


class ErrorCode(IntEnum):
    # 1000-series: request / field validation
    MISSING_REQUEST_ID = 1001
    MISSING_TEXT = 1002
    INVALID_OUTPUT_LANGUAGE = 1003
    TEXT_TOO_SHORT = 1004

    # 2000-series: authentication / authorisation
    AUTHENTICATION_FAILED = 2001
    PERMISSION_DENIED = 2002
    TOKEN_EXPIRED = 2003

    # 3000-series: LLM / provider errors (never exposed externally)
    LLM_PROVIDER_ERROR = 3001
    ALL_PROVIDERS_FAILED = 3002
    LLM_SCHEMA_VALIDATION_ERROR = 3003

    # 4000-series: internal / unexpected errors
    INTERNAL_SERVER_ERROR = 4001
    CONFIGURATION_ERROR = 4002
