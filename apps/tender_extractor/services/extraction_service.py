"""High-level tender extraction service — orchestrates prompt building and LLM calls."""
from __future__ import annotations

import logging

from apps.tender_extractor.llm import LLMOrchestrator
from apps.tender_extractor.llm.base import LLMResponse
from apps.tender_extractor.prompts import PromptBuilder
from apps.tender_extractor.schemas import TenderResponseSchema, LLMMetadataSchema, TenderSchema
from shared.exceptions import AllProvidersFailedException

logger = logging.getLogger(__name__)


class TenderExtractionService:
    """
    Orchestrates:
      1. Prompt construction
      2. LLM call with fallback (via LLMOrchestrator)
      3. Response assembly into TenderResponseSchema
      4. Graceful fallback on total provider failure
    """

    def __init__(
        self,
        orchestrator: LLMOrchestrator | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self._orchestrator = orchestrator or LLMOrchestrator()
        self._prompt_builder = prompt_builder or PromptBuilder()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(
        self,
        *,
        request_id: str,
        text: str,
        output_language: str = "Arabic",
        user: str = "anonymous",
    ) -> TenderResponseSchema:
        """
        Extract tender information from plain text.

        Always returns a TenderResponseSchema — never raises on provider failure.
        """
        prompt = self._prompt_builder.build(
            tender_text=text,
            output_language=output_language,
        )

        try:
            llm_result: LLMResponse = self._orchestrator.extract(
                prompt,
                request_id=request_id,
                user=user,
                output_language=output_language,
            )
            return self._build_response(request_id, llm_result)

        except AllProvidersFailedException:
            logger.error(
                "Returning default tender payload after total provider failure",
                extra={"request_id": request_id},
            )
            return self._default_response(request_id)

        except Exception as exc:
            logger.exception(
                "Unexpected error in extraction service",
                extra={"request_id": request_id, "error": str(exc)},
            )
            from shared.integrations.slack_client import slack_client
            slack_client.alert_unexpected_exception(request_id=request_id, error=str(exc))
            return self._default_response(request_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_response(request_id: str, result: LLMResponse) -> TenderResponseSchema:
        return TenderResponseSchema(
            request_id=request_id,
            tender=result.tender,
            llm_general_fields=LLMMetadataSchema(
                api_time=round(result.api_time, 3),
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                model_name=result.model_name,
                provider=result.provider,
            ),
        )

    @staticmethod
    def _default_response(request_id: str) -> TenderResponseSchema:
        return TenderResponseSchema(
            request_id=request_id,
            tender=TenderSchema(),
            llm_general_fields=LLMMetadataSchema(),
        )
