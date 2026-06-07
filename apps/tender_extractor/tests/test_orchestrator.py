"""Tests for LLMOrchestrator fallback logic."""
from unittest.mock import MagicMock, patch

import pytest

from apps.tender_extractor.llm.base import LLMResponse
from apps.tender_extractor.llm.orchestrator import LLMOrchestrator
from apps.tender_extractor.schemas import TenderSchema, LLMMetadataSchema
from shared.exceptions import AllProvidersFailedException, LLMProviderException


def _make_llm_response(provider: str = "groq") -> LLMResponse:
    return LLMResponse(
        tender=TenderSchema(title="Orchestrated Tender"),
        input_tokens=100,
        output_tokens=50,
        model_name="test-model",
        provider=provider,
        api_time=0.5,
    )


class TestLLMOrchestrator:
    def test_primary_provider_succeeds(self):
        primary = MagicMock()
        primary.provider_name = "groq"
        primary._model = "groq-model"
        primary.extract_tender.return_value = _make_llm_response("groq")

        fallback = MagicMock()
        fallback.provider_name = "openai"

        orchestrator = LLMOrchestrator(providers=[primary, fallback])
        result = orchestrator.extract(
            "prompt", request_id="req-1", user="testuser"
        )

        assert result.provider == "groq"
        fallback.extract_tender.assert_not_called()

    def test_fallback_on_primary_failure(self):
        primary = MagicMock()
        primary.provider_name = "groq"
        primary._model = "groq-model"
        primary.extract_tender.side_effect = LLMProviderException("groq", "timeout")

        fallback = MagicMock()
        fallback.provider_name = "openai"
        fallback._model = "openai-model"
        fallback.extract_tender.return_value = _make_llm_response("openai")

        orchestrator = LLMOrchestrator(providers=[primary, fallback])
        result = orchestrator.extract(
            "prompt", request_id="req-1", user="testuser"
        )

        assert result.provider == "openai"

    def test_all_providers_fail_raises(self):
        primary = MagicMock()
        primary.provider_name = "groq"
        primary._model = "groq-model"
        primary.extract_tender.side_effect = LLMProviderException("groq", "error")

        fallback = MagicMock()
        fallback.provider_name = "openai"
        fallback._model = "openai-model"
        fallback.extract_tender.side_effect = LLMProviderException("openai", "error")

        orchestrator = LLMOrchestrator(providers=[primary, fallback])

        with pytest.raises(AllProvidersFailedException):
            orchestrator.extract("prompt", request_id="req-1", user="testuser")

    def test_single_provider_success(self):
        provider = MagicMock()
        provider.provider_name = "groq"
        provider._model = "groq-model"
        provider.extract_tender.return_value = _make_llm_response("groq")

        orchestrator = LLMOrchestrator(providers=[provider])
        result = orchestrator.extract(
            "prompt", request_id="req-2", user="user2"
        )

        assert result.tender.title == "Orchestrated Tender"
