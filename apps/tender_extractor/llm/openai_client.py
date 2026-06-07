"""OpenAI LLM provider client using the official OpenAI SDK with Structured Outputs."""
from __future__ import annotations

import logging
import time
from typing import Optional

from django.conf import settings
from openai import OpenAI
from pydantic import ValidationError

from apps.tender_extractor.schemas import TenderSchema
from apps.tender_extractor.validators import LLMJSONValidator
from shared.exceptions import LLMProviderException

from .base import BaseLLMClient, LLMResponse

logger = logging.getLogger(__name__)


class OpenAILLMClient(BaseLLMClient):
    """
    Uses the OpenAI SDK Structured Outputs feature (json_schema response format)
    to guarantee schema-conformant extraction.
    """

    provider_name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self._api_key: str = api_key or settings.OPENAI_API_KEY
        self._model: str = model or settings.OPENAI_MODEL
        self._client = OpenAI(api_key=self._api_key)
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
            response = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                response_format=TenderSchema,
                temperature=0.0,
                max_tokens=4096,
            )
        except Exception as exc:
            logger.warning(
                "OpenAI API call failed",
                extra={"provider": self.provider_name, "error": str(exc)},
            )
            raise LLMProviderException(self.provider_name, str(exc)) from exc

        elapsed = time.perf_counter() - start

        choice = response.choices[0]
        parsed = choice.message.parsed  # Already a TenderSchema instance

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        if parsed is None:
            # Fallback: try to parse raw content manually
            raw = choice.message.content or "{}"
            import json
            try:
                data = json.loads(raw)
                parsed = self._validator.validate_and_normalise(data)
            except Exception as exc2:
                raise LLMProviderException(self.provider_name, f"Null parsed response: {exc2}") from exc2
        else:
            # Run through normaliser even for parsed responses (date normalisation etc.)
            parsed = self._validator.validate_and_normalise(parsed.model_dump())

        logger.info(
            "OpenAI extraction success",
            extra={
                "provider": self.provider_name,
                "model": self._model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_s": round(elapsed, 3),
            },
        )

        return LLMResponse(
            tender=parsed,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_name=self._model,
            provider=self.provider_name,
            api_time=elapsed,
            raw_content=choice.message.content,
        )
