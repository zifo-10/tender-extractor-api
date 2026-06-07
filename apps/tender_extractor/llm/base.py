"""Abstract base class for LLM provider clients."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from apps.tender_extractor.schemas import TenderSchema


@dataclass
class LLMResponse:
    """Typed container for an LLM extraction result."""

    tender: TenderSchema
    input_tokens: int
    output_tokens: int
    model_name: str
    provider: str
    api_time: float  # seconds
    raw_content: Optional[str] = field(default=None, repr=False)


class BaseLLMClient(ABC):
    """Contract that all LLM provider clients must implement."""

    provider_name: str = "base"

    @abstractmethod
    def extract_tender(
        self,
        prompt: str,
        *,
        output_language: str = "Arabic",
    ) -> LLMResponse:
        """
        Call the provider and return a validated LLMResponse.

        Raises:
            LLMProviderException: on any provider-level failure.
        """
        raise NotImplementedError
