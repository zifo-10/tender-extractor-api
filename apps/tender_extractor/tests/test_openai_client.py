"""Tests for OpenAILLMClient."""
import json
from unittest.mock import MagicMock, patch

import pytest

from apps.tender_extractor.llm.openai_client import OpenAILLMClient
from apps.tender_extractor.llm.base import LLMResponse
from apps.tender_extractor.schemas import TenderSchema
from shared.exceptions import LLMProviderException


def _make_mock_openai_response(parsed: TenderSchema | None = None, content: str | None = None) -> MagicMock:
    usage = MagicMock()
    usage.prompt_tokens = 200
    usage.completion_tokens = 80

    message = MagicMock()
    message.parsed = parsed
    message.content = content or "{}"

    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


class TestOpenAILLMClient:
    @patch("apps.tender_extractor.llm.openai_client.OpenAI")
    def test_successful_extraction_with_parsed(self, MockOpenAI):
        tender = TenderSchema(title="OpenAI Tender", issuer="OpenAI Issuer")
        mock_client = MockOpenAI.return_value
        mock_client.beta.chat.completions.parse.return_value = _make_mock_openai_response(parsed=tender)

        client = OpenAILLMClient(api_key="test-key", model="gpt-4o-mini")
        result = client.extract_tender("Test prompt")

        assert isinstance(result, LLMResponse)
        assert result.provider == "openai"
        assert result.tender.title == "OpenAI Tender"
        assert result.input_tokens == 200
        assert result.output_tokens == 80

    @patch("apps.tender_extractor.llm.openai_client.OpenAI")
    def test_api_failure_raises_provider_exception(self, MockOpenAI):
        mock_client = MockOpenAI.return_value
        mock_client.beta.chat.completions.parse.side_effect = Exception("OpenAI timeout")

        client = OpenAILLMClient(api_key="test-key", model="gpt-4o-mini")
        with pytest.raises(LLMProviderException) as exc_info:
            client.extract_tender("Test prompt")

        assert "openai" in str(exc_info.value).lower()

    @patch("apps.tender_extractor.llm.openai_client.OpenAI")
    def test_null_parsed_falls_back_to_content(self, MockOpenAI):
        """When parsed is None, client should parse raw content."""
        content = json.dumps({"title": "From content", "key_requirements": []})
        mock_client = MockOpenAI.return_value
        mock_client.beta.chat.completions.parse.return_value = _make_mock_openai_response(
            parsed=None, content=content
        )

        client = OpenAILLMClient(api_key="test-key", model="gpt-4o-mini")
        result = client.extract_tender("Test prompt")
        assert result.tender.title == "From content"
