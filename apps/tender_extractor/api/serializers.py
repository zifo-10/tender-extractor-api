"""DRF serializers for the Tender Extractor endpoint."""
from __future__ import annotations

from django.conf import settings
from rest_framework import serializers

from shared.exceptions import InvalidFieldValueException, MissingFieldException


class TenderExtractorRequestSerializer(serializers.Serializer):
    """Validates the incoming extraction request."""

    request_id = serializers.CharField(max_length=255)
    text = serializers.CharField()
    output_language = serializers.CharField(
        required=False,
        default=settings.DEFAULT_OUTPUT_LANGUAGE,
    )

    def validate_request_id(self, value: str) -> str:
        if not value or not value.strip():
            raise MissingFieldException("request_id")
        return value.strip()

    def validate_text(self, value: str) -> str:
        if not value or not value.strip():
            raise MissingFieldException("text")
        if len(value.strip()) < 20:
            raise InvalidFieldValueException(
                "text",
                "text field must contain at least 20 characters",
            )
        return value.strip()

    def validate_output_language(self, value: str) -> str:
        supported = settings.SUPPORTED_OUTPUT_LANGUAGES
        if value not in supported:
            raise InvalidFieldValueException(
                "output_language",
                f"output_language must be one of: {', '.join(supported)}",
            )
        return value


# ---------------------------------------------------------------------------
# Response serializers (for Swagger documentation only — responses are built
# directly from Pydantic models and returned as dicts).
# ---------------------------------------------------------------------------

class BudgetResponseSerializer(serializers.Serializer):
    amount = serializers.FloatField(allow_null=True)
    currency = serializers.CharField()


class ContactResponseSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.CharField()
    phone = serializers.CharField()


class TenderResponseSerializer(serializers.Serializer):
    title = serializers.CharField()
    issuer = serializers.CharField()
    reference_number = serializers.CharField()
    publication_date = serializers.CharField(allow_null=True)
    submission_deadline = serializers.CharField(allow_null=True)
    budget = BudgetResponseSerializer()
    scope_of_work = serializers.CharField()
    key_requirements = serializers.ListField(child=serializers.CharField())
    eligibility_criteria = serializers.ListField(child=serializers.CharField())
    evaluation_criteria = serializers.ListField(child=serializers.CharField())
    deliverables = serializers.ListField(child=serializers.CharField())
    contact = ContactResponseSerializer()


class LLMGeneralFieldsSerializer(serializers.Serializer):
    api_time = serializers.FloatField()
    input_tokens = serializers.IntegerField()
    output_tokens = serializers.IntegerField()
    model_name = serializers.CharField()


class TenderExtractorResponseSerializer(serializers.Serializer):
    request_id = serializers.CharField()
    tender = TenderResponseSerializer()
    llm_general_fields = LLMGeneralFieldsSerializer()


class ValidationErrorResponseSerializer(serializers.Serializer):
    response_code = serializers.IntegerField()
    message = serializers.CharField()
