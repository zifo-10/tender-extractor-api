"""UsageTrackingMiddleware — records every API hit after response is sent."""
from __future__ import annotations

import logging
import time
from typing import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

_TRACKED_PATH_PREFIXES = ("/api/v1/",)


class UsageTrackingMiddleware:
    """
    Lightweight middleware that records API usage after each response.

    Tracking is best-effort: failures are logged but never bubble up.
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.perf_counter()
        response: HttpResponse = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if self._should_track(request):
            self._record(request, response, elapsed_ms)

        return response

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @staticmethod
    def _should_track(request: HttpRequest) -> bool:
        return any(request.path.startswith(p) for p in _TRACKED_PATH_PREFIXES)

    @staticmethod
    def _record(request: HttpRequest, response: HttpResponse, latency_ms: float) -> None:
        try:
            from apps.usage_tracking.services import UsageTrackingService

            status_code: int = response.status_code
            success = 200 <= status_code < 300
            bad_request = status_code == 400

            api_name = request.path.rstrip("/")

            UsageTrackingService.record_api_hit(
                user=getattr(request, "user", None),
                api_name=api_name,
                success=success,
                bad_request=bad_request,
            )
        except Exception as exc:
            logger.debug("Usage tracking middleware error (non-critical): %s", exc)
