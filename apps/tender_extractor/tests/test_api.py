"""Integration tests for the Tender Extractor API endpoint."""
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.tender_extractor.schemas import TenderSchema, LLMMetadataSchema, TenderResponseSchema

User = get_user_model()


def _get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


VALID_REQUEST = {
    "request_id": "req-test-001",
    "text": (
        "Ministry of Finance invites bids for the supply and delivery of IT equipment. "
        "Reference: MOF-2024-001. Deadline: 2024-02-15. Budget: SAR 500,000."
    ),
    "output_language": "English",
}

MOCK_RESPONSE = TenderResponseSchema(
    request_id="req-test-001",
    tender=TenderSchema(
        title="IT Equipment Supply",
        issuer="Ministry of Finance",
        reference_number="MOF-2024-001",
    ),
    llm_general_fields=LLMMetadataSchema(
        api_time=1.0,
        input_tokens=100,
        output_tokens=50,
        model_name="test-model",
        provider="groq",
    ),
)


@pytest.mark.django_db
class TestTenderExtractorView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.token = _get_tokens_for_user(self.user)
        self.url = reverse("tender-extractor")

    def _auth_headers(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    @patch("apps.tender_extractor.api.views.TenderExtractionService.extract")
    def test_successful_extraction(self, mock_extract):
        mock_extract.return_value = MOCK_RESPONSE

        response = self.client.post(
            self.url,
            data=VALID_REQUEST,
            format="json",
            **self._auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["request_id"] == "req-test-001"
        assert "tender" in data
        assert "llm_general_fields" in data

    def test_unauthenticated_request_rejected(self):
        response = self.client.post(self.url, data=VALID_REQUEST, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_request_id(self):
        payload = {**VALID_REQUEST}
        del payload["request_id"]
        response = self.client.post(
            self.url, data=payload, format="json", **self._auth_headers()
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "response_code" in data
        assert "message" in data

    def test_missing_text(self):
        payload = {**VALID_REQUEST}
        del payload["text"]
        response = self.client.post(
            self.url, data=payload, format="json", **self._auth_headers()
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["response_code"] == 1001  # MISSING_REQUEST_ID or similar field code

    def test_invalid_output_language(self):
        payload = {**VALID_REQUEST, "output_language": "French"}
        response = self.client.post(
            self.url, data=payload, format="json", **self._auth_headers()
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.tender_extractor.api.views.TenderExtractionService.extract")
    def test_all_providers_fail_returns_200_with_default(self, mock_extract):
        """On total LLM failure, the service returns a default response (HTTP 200)."""
        from apps.tender_extractor.services.extraction_service import TenderExtractionService

        default_response = TenderResponseSchema(
            request_id="req-test-001",
            tender=TenderSchema(),
            llm_general_fields=LLMMetadataSchema(),
        )
        mock_extract.return_value = default_response

        response = self.client.post(
            self.url,
            data=VALID_REQUEST,
            format="json",
            **self._auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["tender"]["title"] == ""
