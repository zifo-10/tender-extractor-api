"""Groq LLM provider client using the official Groq SDK."""
from __future__ import annotations

import json
import logging
import time
from typing import Optional

from django.conf import settings
from groq import Groq

from apps.tender_extractor.schemas import TenderSchema
from apps.tender_extractor.validators import LLMJSONValidator
from shared.exceptions import LLMProviderException

from .base import BaseLLMClient, LLMResponse

logger = logging.getLogger(__name__)

_RESPONSE_SCHEMA = TenderSchema.model_json_schema()


class GroqLLMClient(BaseLLMClient):
    """Uses the Groq SDK to call Groq-hosted models with structured JSON output."""

    provider_name = "groq"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self._api_key: str = api_key or settings.GROQ_API_KEY
        self._model: str = model or settings.GROQ_MODEL
        self._client = Groq(api_key=self._api_key)
        self._validator = LLMJSONValidator()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def extract_tender(
        self,
        prompt: str,
        *,
        output_language: str = "Arabic",
    ) -> LLMResponse:
        start = time.perf_counter()
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=4096,
            )
        except Exception as exc:
            logger.warning(
                "Groq API call failed",
                extra={"provider": self.provider_name, "error": str(exc)},
            )
            raise LLMProviderException(self.provider_name, str(exc)) from exc

        elapsed = time.perf_counter() - start

        choice = response.choices[0]
        raw_content: str = choice.message.content or "{}"

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        tender = self._parse_and_validate(raw_content)

        logger.info(
            "Groq extraction success",
            extra={
                "provider": self.provider_name,
                "model": self._model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_s": round(elapsed, 3),
            },
        )

        return LLMResponse(
            tender=tender,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_name=self._model,
            provider=self.provider_name,
            api_time=elapsed,
            raw_content=raw_content,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_and_validate(self, raw: str) -> TenderSchema:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Groq returned invalid JSON",
                extra={"provider": self.provider_name, "error": str(exc)},
            )
            raise LLMProviderException(self.provider_name, f"Invalid JSON: {exc}") from exc

        return self._validator.validate_and_normalise(data)
