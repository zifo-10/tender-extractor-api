"""Usage tracking aggregation service."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.usage_tracking.models import APIUsage, LLMCallLog
from apps.usage_tracking.services.pricing_service import PricingService

logger = logging.getLogger(__name__)
User = get_user_model()


def _floor_to_hour(dt: datetime) -> datetime:
    """Truncate a datetime to the start of its UTC hour."""
    return dt.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


class UsageTrackingService:
    """
    Persists and aggregates API usage records.

    All methods are designed to be non-blocking — failures are logged
    but never propagated to the caller.
    """

    @classmethod
    def record_api_hit(
        cls,
        *,
        user: Optional[object],
        api_name: str,
        success: bool,
        bad_request: bool,
        input_tokens: int = 0,
        output_tokens: int = 0,
        provider: str = "",
        model_name: str = "",
        cost_usd: float = 0.0,
        request_id: str = "",
        latency_ms: float = 0.0,
        fallback_used: bool = False,
    ) -> None:
        """Upsert an hourly usage bucket and optionally log the LLM call."""
        try:
            cls._upsert_hourly_bucket(
                user=user,
                api_name=api_name,
                success=success,
                bad_request=bad_request,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )
            if provider:
                cls._log_llm_call(
                    user=user,
                    request_id=request_id,
                    provider=provider,
                    model_name=model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                    success=success,
                    fallback_used=fallback_used,
                )
        except Exception as exc:
            logger.warning(
                "Usage tracking failed (non-critical)",
                extra={"error": str(exc), "api_name": api_name},
            )

    @classmethod
    def record_llm_usage(
        cls,
        *,
        user: Optional[object],
        api_name: str,
        request_id: str,
        provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float,
        fallback_used: bool = False,
    ) -> None:
        """
        Update the current hour's usage bucket with LLM token/cost data
        (does NOT increment hit counters — the middleware handles those).
        Also persists a LLMCallLog row for per-request detail.
        """
        try:
            cls._add_tokens_to_bucket(
                user=user,
                api_name=api_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )
            cls._log_llm_call(
                user=user,
                request_id=request_id,
                provider=provider,
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                success=True,
                fallback_used=fallback_used,
            )
        except Exception as exc:
            logger.warning(
                "LLM usage tracking failed (non-critical)",
                extra={"error": str(exc), "request_id": request_id},
            )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @classmethod
    @transaction.atomic
    def _upsert_hourly_bucket(
        cls,
        *,
        user,
        api_name: str,
        success: bool,
        bad_request: bool,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> None:
        hour = _floor_to_hour(datetime.now(tz=timezone.utc))
        obj, _ = APIUsage.objects.select_for_update().get_or_create(
            user=user if (hasattr(user, "pk") and user.is_authenticated) else None,
            api_name=api_name,
            hour_timestamp=hour,
            defaults={
                "total_hits": 0,
                "success_hits": 0,
                "bad_request_hits": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": Decimal("0"),
            },
        )
        obj.total_hits += 1
        if success:
            obj.success_hits += 1
        if bad_request:
            obj.bad_request_hits += 1
        obj.total_input_tokens += input_tokens
        obj.total_output_tokens += output_tokens
        obj.total_cost_usd += Decimal(str(cost_usd))
        obj.save(
            update_fields=[
                "total_hits",
                "success_hits",
                "bad_request_hits",
                "total_input_tokens",
                "total_output_tokens",
                "total_cost_usd",
                "updated_at",
            ]
        )

    @classmethod
    @transaction.atomic
    def _add_tokens_to_bucket(
        cls,
        *,
        user,
        api_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> None:
        """Update token/cost fields on the current hour's bucket (no hit increment)."""
        hour = _floor_to_hour(datetime.now(tz=timezone.utc))
        resolved_user = user if (hasattr(user, "pk") and user.is_authenticated) else None
        obj, _ = APIUsage.objects.select_for_update().get_or_create(
            user=resolved_user,
            api_name=api_name,
            hour_timestamp=hour,
            defaults={
                "total_hits": 0,
                "success_hits": 0,
                "bad_request_hits": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": Decimal("0"),
            },
        )
        obj.total_input_tokens += input_tokens
        obj.total_output_tokens += output_tokens
        obj.total_cost_usd += Decimal(str(cost_usd))
        obj.save(update_fields=["total_input_tokens", "total_output_tokens", "total_cost_usd", "updated_at"])

    @classmethod
    def _log_llm_call(
        cls,
        *,
        user,
        request_id: str,
        provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float,
        success: bool,
        fallback_used: bool,
    ) -> None:
        LLMCallLog.objects.create(
            user=user if (hasattr(user, "pk") and user.is_authenticated) else None,
            request_id=request_id,
            provider=provider,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=Decimal(str(cost_usd)),
            latency_ms=latency_ms,
            success=success,
            fallback_used=fallback_used,
        )
