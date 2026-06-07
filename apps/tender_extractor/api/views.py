"""Tender Extractor API view."""
from __future__ import annotations

import logging

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.tender_extractor.api.serializers import (
    TenderExtractorRequestSerializer,
    TenderExtractorResponseSerializer,
    ValidationErrorResponseSerializer,
)
from apps.tender_extractor.services import TenderExtractionService
from shared.exceptions import MissingFieldException, ValidationException

logger = logging.getLogger(__name__)


class TenderExtractorView(APIView):
    """
    POST /api/v1/tender-extractor/

    Receives a tender document as plain text and returns structured extraction
    results using an LLM backend (Groq primary, OpenAI fallback).
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # Lazy — only instantiated on first real request, not during schema generation
    _service: "TenderExtractionService | None" = None

    def _get_service(self) -> "TenderExtractionService":
        if self._service is None:
            self._service = TenderExtractionService()
        return self._service

    @extend_schema(
        tags=["Tender Extractor"],
        summary="Extract structured data from a tender document",
        description=(
            "Submit a tender / RFP / RFQ document as plain text. "
            "The endpoint uses LLMs (Groq → OpenAI fallback) to extract "
            "structured procurement information. "
            "Requires a valid JWT Bearer token."
        ),
        request=TenderExtractorRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=TenderExtractorResponseSerializer,
                description="Successful extraction (may contain empty fields on LLM failure)",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "request_id": "req-001",
                            "tender": {
                                "title": "Supply of IT Equipment",
                                "issuer": "Ministry of Finance",
                                "reference_number": "MOF-2024-001",
                                "publication_date": "2024-01-15",
                                "submission_deadline": "2024-02-15",
                                "budget": {"amount": 500000.0, "currency": "SAR"},
                                "scope_of_work": "Supply and installation of servers",
                                "key_requirements": ["ISO 9001 certified", "5+ years experience"],
                                "eligibility_criteria": ["Registered company in KSA"],
                                "evaluation_criteria": ["Technical 60%", "Financial 40%"],
                                "deliverables": ["Equipment", "Installation", "Training"],
                                "contact": {
                                    "name": "Ahmed Al-Rashid",
                                    "email": "tenders@mof.gov.sa",
                                    "phone": "+966-11-000-0000",
                                },
                            },
                            "llm_general_fields": {
                                "api_time": 1.23,
                                "input_tokens": 1500,
                                "output_tokens": 400,
                                "model_name": "openai/gpt-oss-120b",
                            },
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer,
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Missing text",
                        value={"response_code": 1002, "message": "text field is required"},
                    )
                ],
            ),
            401: OpenApiResponse(description="Unauthorised — invalid or missing JWT token"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = TenderExtractorRequestSerializer(data=request.data)

        if not serializer.is_valid():
            # Map DRF validation errors to our custom format
            first_field, errors = next(iter(serializer.errors.items()))
            first_error = errors[0] if errors else "Validation error"
            exc = self._map_field_error(first_field, str(first_error))
            return Response(exc.to_dict(), status=status.HTTP_400_BAD_REQUEST)

        validated = serializer.validated_data
        user_str = request.user.username if request.user.is_authenticated else "anonymous"

        result = self._get_service().extract(
            request_id=validated["request_id"],
            text=validated["text"],
            output_language=validated.get("output_language", "Arabic"),
            user=user_str,
        )

        # Persist LLM token/cost data to the usage tracking DB
        if result.llm_general_fields.input_tokens or result.llm_general_fields.output_tokens:
            from apps.usage_tracking.services import UsageTrackingService
            from apps.usage_tracking.services.pricing_service import PricingService

            provider = result.llm_general_fields.provider
            cost = PricingService.calculate_cost(
                provider=provider,
                input_tokens=result.llm_general_fields.input_tokens,
                output_tokens=result.llm_general_fields.output_tokens,
            )
            UsageTrackingService.record_llm_usage(
                user=request.user,
                api_name=request.path.rstrip("/"),
                request_id=validated["request_id"],
                provider=provider,
                model_name=result.llm_general_fields.model_name,
                input_tokens=result.llm_general_fields.input_tokens,
                output_tokens=result.llm_general_fields.output_tokens,
                cost_usd=cost,
                latency_ms=result.llm_general_fields.api_time * 1000,
                fallback_used=(provider != "groq"),
            )

        # Exclude internal 'provider' field from llm_general_fields response
        response_payload = result.model_dump(exclude={"llm_general_fields": {"provider"}})
        return Response(response_payload, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_field_error(field: str, message: str) -> ValidationException:
        from shared.exceptions import MissingFieldException, InvalidFieldValueException
        from shared.exceptions.error_codes import ErrorCode

        if "required" in message.lower():
            return MissingFieldException(field)

        field_code_map = {
            "output_language": ErrorCode.INVALID_OUTPUT_LANGUAGE,
            "text": ErrorCode.TEXT_TOO_SHORT,
            "request_id": ErrorCode.MISSING_REQUEST_ID,
        }
        code = field_code_map.get(field, ErrorCode.MISSING_REQUEST_ID)
        return InvalidFieldValueException(field, message)
