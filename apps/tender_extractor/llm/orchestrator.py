"""LLM Orchestrator — manages provider chain with fallback."""
from __future__ import annotations

import logging
from typing import Optional

from shared.exceptions import AllProvidersFailedException, LLMProviderException
from shared.integrations.slack_client import slack_client
from shared.logging.request_logger import log_llm_call

from .base import BaseLLMClient, LLMResponse
from .groq_client import GroqLLMClient
from .openai_client import OpenAILLMClient

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    Executes extraction through an ordered list of providers.

    Primary:  Groq
    Fallback: OpenAI

    On total failure raises AllProvidersFailedException which is handled
    gracefully by the API view.
    """

    def __init__(
        self,
        providers: Optional[list[BaseLLMClient]] = None,
    ) -> None:
        if providers is not None:
            self._providers = providers
        else:
            self._providers: list[BaseLLMClient] = [
                GroqLLMClient(),
                OpenAILLMClient(),
            ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(
        self,
        prompt: str,
        *,
        request_id: str,
        user: str,
        output_language: str = "Arabic",
    ) -> LLMResponse:
        """
        Try each provider in order.  Log every attempt.
        Raise AllProvidersFailedException only after all providers fail.
        """
        last_exception: Optional[Exception] = None
        fallback = False

        for provider in self._providers:
            try:
                result = provider.extract_tender(prompt, output_language=output_language)

                # Calculate cost
                from apps.usage_tracking.services.pricing_service import PricingService
                cost = PricingService.calculate_cost(
                    provider=result.provider,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                )

                log_llm_call(
                    request_id=request_id,
                    user=user,
                    provider=result.provider,
                    model=result.model_name,
                    latency_ms=result.api_time * 1000,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    cost_usd=cost,
                    fallback=fallback,
                    success=True,
                )
                return result

            except LLMProviderException as exc:
                logger.warning(
                    "Provider failed, trying next",
                    extra={
                        "provider": provider.provider_name,
                        "request_id": request_id,
                        "error": str(exc),
                        "fallback": fallback,
                    },
                )
                log_llm_call(
                    request_id=request_id,
                    user=user,
                    provider=provider.provider_name,
                    model=getattr(provider, "_model", "unknown"),
                    latency_ms=0,
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd=0.0,
                    fallback=fallback,
                    success=False,
                    error=str(exc),
                )
                last_exception = exc
                fallback = True

        # All providers failed
        logger.error(
            "All LLM providers failed",
            extra={"request_id": request_id, "user": user},
        )
        slack_client.alert_all_providers_failed(request_id=request_id, user=user)
        raise AllProvidersFailedException(
            f"All providers failed. Last error: {last_exception}"
        )
