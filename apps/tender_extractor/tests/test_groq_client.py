"""Tests for GroqLLMClient."""
import json
from unittest.mock import MagicMock, patch

import pytest

from apps.tender_extractor.llm.groq_client import GroqLLMClient
from apps.tender_extractor.llm.base import LLMResponse
from shared.exceptions import LLMProviderException


SAMPLE_EXTRACTION = {
    "title": "Test Tender",
    "issuer": "Test Issuer",
    "reference_number": "REF-001",
    "publication_date": None,
    "submission_deadline": None,
    "budget": {"amount": 10000.0, "currency": "SAR"},
    "scope_of_work": "Testing scope",
    "key_requirements": [],
    "eligibility_criteria": [],
    "evaluation_criteria": [],
    "deliverables": [],
    "contact": {"name": "", "email": "", "phone": ""},
}


def _make_mock_groq_response(content: str) -> MagicMock:
    usage = MagicMock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 50

    message = MagicMock()
    message.content = content

    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


class TestGroqLLMClient:
    @patch("apps.tender_extractor.llm.groq_client.Groq")
    def test_successful_extraction(self, MockGroq):
        mock_client = MockGroq.return_value
        mock_client.chat.completions.create.return_value = _make_mock_groq_response(
            json.dumps(SAMPLE_EXTRACTION)
        )

        client = GroqLLMClient(api_key="test-key", model="test-model")
        result = client.extract_tender("Test prompt")

        assert isinstance(result, LLMResponse)
        assert result.provider == "groq"
        assert result.tender.title == "Test Tender"
        assert result.input_tokens == 100
        assert result.output_tokens == 50

    @patch("apps.tender_extractor.llm.groq_client.Groq")
    def test_api_failure_raises_provider_exception(self, MockGroq):
        mock_client = MockGroq.return_value
        mock_client.chat.completions.create.side_effect = Exception("API error")

        client = GroqLLMClient(api_key="test-key", model="test-model")
        with pytest.raises(LLMProviderException) as exc_info:
            client.extract_tender("Test prompt")

        assert "groq" in str(exc_info.value).lower()

    @patch("apps.tender_extractor.llm.groq_client.Groq")
    def test_invalid_json_raises_provider_exception(self, MockGroq):
        mock_client = MockGroq.return_value
        mock_client.chat.completions.create.return_value = _make_mock_groq_response(
            "not valid json {{{"
        )

        client = GroqLLMClient(api_key="test-key", model="test-model")
        with pytest.raises(LLMProviderException):
            client.extract_tender("Test prompt")

    @patch("apps.tender_extractor.llm.groq_client.Groq")
    def test_partial_response_still_returns_schema(self, MockGroq):
        mock_client = MockGroq.return_value
        mock_client.chat.completions.create.return_value = _make_mock_groq_response(
            json.dumps({"title": "Partial"})
        )

        client = GroqLLMClient(api_key="test-key", model="test-model")
        result = client.extract_tender("Test prompt")
        assert result.tender.title == "Partial"
        assert result.tender.key_requirements == []
