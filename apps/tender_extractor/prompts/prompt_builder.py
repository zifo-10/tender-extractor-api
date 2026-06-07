"""Provider-independent prompt builder for tender extraction."""
from __future__ import annotations

import json

from apps.tender_extractor.schemas import TenderSchema


_DEFAULT_OUTPUT_JSON = json.dumps(
    {
        "title": "",
        "issuer": "",
        "reference_number": "",
        "publication_date": None,
        "submission_deadline": None,
        "budget": {"amount": None, "currency": ""},
        "scope_of_work": "",
        "key_requirements": [],
        "eligibility_criteria": [],
        "evaluation_criteria": [],
        "deliverables": [],
        "contact": {"name": "", "email": "", "phone": ""},
    },
    ensure_ascii=False,
    indent=2,
)

_LANGUAGE_INSTRUCTIONS = {
    "Arabic": (
        "Respond EXCLUSIVELY in Arabic. "
        "All field values must be in Arabic. "
        "Field keys must remain in English exactly as shown in the schema."
    ),
    "English": (
        "Respond EXCLUSIVELY in English. "
        "All field values must be in English. "
        "Field keys must remain in English exactly as shown in the schema."
    ),
}


class PromptBuilder:
    """
    Constructs structured prompts for LLM tender extraction.

    Sections:
        task_definition
        default_output_json
        output_language
        guidelines
        invalid_input_handling
        important_notes
    """

    def build(
        self,
        *,
        tender_text: str,
        output_language: str = "Arabic",
    ) -> str:
        """Return a complete extraction prompt."""
        language_instruction = _LANGUAGE_INSTRUCTIONS.get(
            output_language,
            _LANGUAGE_INSTRUCTIONS["Arabic"],
        )

        schema_description = json.dumps(
            TenderSchema.model_json_schema(),
            ensure_ascii=False,
            indent=2,
        )

        sections = [
            self._task_definition(),
            self._default_output_json(),
            self._output_language(language_instruction),
            self._guidelines(),
            self._invalid_input_handling(),
            self._important_notes(),
            self._tender_document(tender_text),
        ]

        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def _task_definition(self) -> str:
        return (
            "## TASK DEFINITION\n"
            "You are an expert procurement analyst specialising in tender, "
            "RFP, and RFQ document extraction.\n"
            "Extract ALL available structured information from the provided tender "
            "document and return it as a single, valid JSON object that strictly "
            "conforms to the schema below."
        )

    def _default_output_json(self) -> str:
        return (
            "## REQUIRED OUTPUT SCHEMA\n"
            "Return ONLY a JSON object matching this exact structure "
            "(no markdown, no code fences, no extra keys):\n"
            f"{_DEFAULT_OUTPUT_JSON}"
        )

    def _output_language(self, instruction: str) -> str:
        return f"## OUTPUT LANGUAGE\n{instruction}"

    def _guidelines(self) -> str:
        return (
            "## EXTRACTION GUIDELINES\n"
            "- Extract every field present in the document; leave others as empty string or null.\n"
            "- Dates MUST be formatted as YYYY-MM-DD. If only partial date info is available, do your best.\n"
            "- budget.amount must be a numeric value (float or null). Remove currency symbols.\n"
            "- budget.currency must be the ISO 4217 code (e.g. SAR, USD, EUR) or empty string.\n"
            "- key_requirements, eligibility_criteria, evaluation_criteria, and deliverables must be "
            "arrays of strings. Never nest objects inside these arrays.\n"
            "- contact fields (name, email, phone) should be extracted from the issuer section.\n"
            "- Do NOT invent information not present in the document.\n"
            "- Be concise but complete."
        )

    def _invalid_input_handling(self) -> str:
        return (
            "## INVALID INPUT HANDLING\n"
            "If the document does not appear to be a tender/RFP/RFQ document, "
            "return the default empty JSON structure without any modification. "
            "Do not return an error message."
        )

    def _important_notes(self) -> str:
        return (
            "## IMPORTANT NOTES\n"
            "- Return ONLY the JSON object — no explanation, no commentary.\n"
            "- Do not wrap the JSON in markdown code fences.\n"
            "- Do not add fields not present in the schema.\n"
            "- All JSON keys must remain in English even if values are in another language."
        )

    def _tender_document(self, text: str) -> str:
        return f"## TENDER DOCUMENT\n{text}"
