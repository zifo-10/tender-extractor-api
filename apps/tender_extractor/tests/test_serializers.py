"""Tests for DRF serializers."""
import pytest

from apps.tender_extractor.api.serializers import TenderExtractorRequestSerializer
from shared.exceptions import MissingFieldException, InvalidFieldValueException


@pytest.mark.django_db
class TestTenderExtractorRequestSerializer:
    def test_valid_data(self):
        data = {
            "request_id": "req-001",
            "text": "This is a valid tender document with enough characters to pass validation.",
            "output_language": "Arabic",
        }
        serializer = TenderExtractorRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_default_language_arabic(self):
        data = {
            "request_id": "req-001",
            "text": "This is a valid tender document with enough characters.",
        }
        serializer = TenderExtractorRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["output_language"] == "Arabic"

    def test_english_language_valid(self):
        data = {
            "request_id": "req-001",
            "text": "This is a valid tender document with enough characters.",
            "output_language": "English",
        }
        serializer = TenderExtractorRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_request_id(self):
        data = {
            "text": "Some tender text with enough characters here.",
        }
        serializer = TenderExtractorRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "request_id" in serializer.errors

    def test_missing_text(self):
        data = {"request_id": "req-001"}
        serializer = TenderExtractorRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "text" in serializer.errors

    def test_invalid_language(self):
        data = {
            "request_id": "req-001",
            "text": "Valid tender text that is long enough.",
            "output_language": "French",
        }
        serializer = TenderExtractorRequestSerializer(data=data)
        assert not serializer.is_valid()

    def test_text_too_short(self):
        data = {
            "request_id": "req-001",
            "text": "Short",
        }
        serializer = TenderExtractorRequestSerializer(data=data)
        assert not serializer.is_valid()
