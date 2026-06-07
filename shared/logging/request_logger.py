"""Structured request/LLM event logger."""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Generator, Optional

logger = logging.getLogger("apps.tender_extractor")


def log_llm_call(
    *,
    request_id: str,
    user: str,
    provider: str,
    model: str,
    latency_ms: float,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    fallback: bool = False,
    success: bool = True,
    error: Optional[str] = None,
) -> None:
    """Emit a structured JSON log entry for every LLM call."""
    logger.info(
        "llm_call",
        extra={
            "event": "llm_call",
            "request_id": request_id,
            "user": user,
            "provider": provider,
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost_usd, 6),
            "fallback": fallback,
            "success": success,
            "error": error,
        },
    )


def log_request(
    *,
    request_id: str,
    user: str,
    endpoint: str,
    status_code: int,
    latency_ms: float,
) -> None:
    """Emit a structured log entry for an API request."""
    logger.info(
        "api_request",
        extra={
            "event": "api_request",
            "request_id": request_id,
            "user": user,
            "endpoint": endpoint,
            "status_code": status_code,
            "latency_ms": round(latency_ms, 2),
        },
    )


@contextmanager
def timer() -> Generator[dict, None, None]:
    """Context manager that records elapsed wall time in milliseconds."""
    result: dict = {}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["elapsed_ms"] = (time.perf_counter() - start) * 1000
