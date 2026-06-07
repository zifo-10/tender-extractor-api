"""Cost calculation service — configurable per-million-token pricing."""
from __future__ import annotations

from django.conf import settings


class PricingService:
    """
    Calculates the USD cost for an LLM call based on configurable pricing.

    Pricing is read from Django settings (set from environment variables):
      OPENAI_INPUT_COST_PER_MILLION
      OPENAI_OUTPUT_COST_PER_MILLION
      GROQ_INPUT_COST_PER_MILLION
      GROQ_OUTPUT_COST_PER_MILLION
    """

    # Fallback defaults (USD per million tokens)
    _DEFAULTS = {
        "openai": {"input": 0.40, "output": 1.60},
        "groq": {"input": 0.05, "output": 0.10},
    }

    @classmethod
    def get_pricing(cls, provider: str) -> dict[str, float]:
        """Return per-million pricing for a given provider."""
        provider = provider.lower()
        if provider == "openai":
            return {
                "input": float(
                    getattr(settings, "OPENAI_INPUT_COST_PER_MILLION", cls._DEFAULTS["openai"]["input"])
                ),
                "output": float(
                    getattr(settings, "OPENAI_OUTPUT_COST_PER_MILLION", cls._DEFAULTS["openai"]["output"])
                ),
            }
        elif provider == "groq":
            return {
                "input": float(
                    getattr(settings, "GROQ_INPUT_COST_PER_MILLION", cls._DEFAULTS["groq"]["input"])
                ),
                "output": float(
                    getattr(settings, "GROQ_OUTPUT_COST_PER_MILLION", cls._DEFAULTS["groq"]["output"])
                ),
            }
        # Unknown provider — no cost
        return {"input": 0.0, "output": 0.0}

    @classmethod
    def calculate_cost(
        cls,
        *,
        provider: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Return the USD cost for a single LLM call."""
        pricing = cls.get_pricing(provider)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 8)
