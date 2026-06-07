"""LLMJSONValidator — schema validation, type coercion and normalisation."""
from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from apps.tender_extractor.schemas import TenderSchema
from shared.exceptions import LLMProviderException
from shared.exceptions.error_codes import ErrorCode

logger = logging.getLogger(__name__)

_KNOWN_KEYS = frozenset(TenderSchema.model_fields.keys())


class LLMJSONValidator:
    """
    Responsibilities:
    - Validate schema conformance
    - Validate and coerce types
    - Normalise date strings to YYYY-MM-DD
    - Default missing arrays to []
    - Remove unknown fields
    - Repair minor formatting issues
    - Gracefully handle invalid responses
    """

    def validate_and_normalise(self, data: dict[str, Any]) -> TenderSchema:
        """
        Takes a raw dict from an LLM and returns a validated TenderSchema.

        Raises LLMProviderException on unrecoverable schema failures.
        """
        if not isinstance(data, dict):
            logger.warning("LLM returned non-dict response; defaulting.")
            return TenderSchema()

        cleaned = self._remove_unknown_fields(data)
        cleaned = self._ensure_arrays(cleaned)
        cleaned = self._repair_budget(cleaned)
        cleaned = self._repair_contact(cleaned)

        try:
            return TenderSchema(**cleaned)
        except ValidationError as exc:
            logger.warning(
                "Pydantic validation failed on LLM output — attempting lenient parse",
                extra={"errors": exc.errors()},
            )
            # Lenient: build from what we can
            return self._lenient_parse(cleaned, exc)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _remove_unknown_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """Strip any keys that are not in TenderSchema."""
        return {k: v for k, v in data.items() if k in _KNOWN_KEYS}

    def _ensure_arrays(self, data: dict[str, Any]) -> dict[str, Any]:
        """Guarantee that array fields are lists."""
        array_fields = [
            "key_requirements",
            "eligibility_criteria",
            "evaluation_criteria",
            "deliverables",
        ]
        for field in array_fields:
            val = data.get(field)
            if val is None:
                data[field] = []
            elif not isinstance(val, list):
                # If it's a string, try splitting on newlines/semicolons
                if isinstance(val, str) and val.strip():
                    data[field] = [
                        item.strip()
                        for item in val.replace(";", "\n").splitlines()
                        if item.strip()
                    ]
                else:
                    data[field] = []
        return data

    def _repair_budget(self, data: dict[str, Any]) -> dict[str, Any]:
        """Ensure budget is a dict."""
        budget = data.get("budget")
        if budget is None:
            data["budget"] = {"amount": None, "currency": ""}
        elif not isinstance(budget, dict):
            data["budget"] = {"amount": None, "currency": ""}
        return data

    def _repair_contact(self, data: dict[str, Any]) -> dict[str, Any]:
        """Ensure contact is a dict."""
        contact = data.get("contact")
        if contact is None:
            data["contact"] = {"name": "", "email": "", "phone": ""}
        elif not isinstance(contact, dict):
            data["contact"] = {"name": "", "email": "", "phone": ""}
        return data

    def _lenient_parse(
        self,
        data: dict[str, Any],
        original_error: ValidationError,
    ) -> TenderSchema:
        """Build a TenderSchema setting erroneous fields to their defaults."""
        safe_data: dict[str, Any] = {}
        defaults = TenderSchema()

        for field_name in TenderSchema.model_fields:
            try:
                safe_data[field_name] = data.get(field_name, getattr(defaults, field_name))
            except Exception:
                safe_data[field_name] = getattr(defaults, field_name)

        try:
            return TenderSchema(**safe_data)
        except ValidationError:
            logger.error(
                "Lenient parse also failed — returning empty TenderSchema",
                extra={"original_errors": original_error.errors()},
            )
            return TenderSchema()
