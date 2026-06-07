"""Tests for PromptBuilder."""
import pytest

from apps.tender_extractor.prompts import PromptBuilder


@pytest.fixture
def builder():
    return PromptBuilder()


class TestPromptBuilder:
    def test_build_returns_string(self, builder):
        prompt = builder.build(tender_text="Sample tender document text here.", output_language="Arabic")
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_prompt_contains_task_definition(self, builder):
        prompt = builder.build(tender_text="Tender text", output_language="English")
        assert "TASK DEFINITION" in prompt

    def test_prompt_contains_output_schema(self, builder):
        prompt = builder.build(tender_text="Tender text", output_language="English")
        assert "REQUIRED OUTPUT SCHEMA" in prompt

    def test_prompt_contains_tender_document(self, builder):
        tender_text = "This is a unique tender document for testing."
        prompt = builder.build(tender_text=tender_text, output_language="English")
        assert tender_text in prompt

    def test_arabic_language_instruction(self, builder):
        prompt = builder.build(tender_text="text", output_language="Arabic")
        assert "Arabic" in prompt

    def test_english_language_instruction(self, builder):
        prompt = builder.build(tender_text="text", output_language="English")
        assert "English" in prompt

    def test_guidelines_included(self, builder):
        prompt = builder.build(tender_text="text", output_language="English")
        assert "EXTRACTION GUIDELINES" in prompt

    def test_invalid_handling_included(self, builder):
        prompt = builder.build(tender_text="text", output_language="English")
        assert "INVALID INPUT HANDLING" in prompt

    def test_important_notes_included(self, builder):
        prompt = builder.build(tender_text="text", output_language="English")
        assert "IMPORTANT NOTES" in prompt

    def test_default_language_is_arabic(self, builder):
        prompt = builder.build(tender_text="text")
        assert "Arabic" in prompt
