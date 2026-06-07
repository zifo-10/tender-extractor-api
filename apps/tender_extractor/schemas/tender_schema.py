"""Pydantic v2 schemas for tender extraction."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BudgetSchema(BaseModel):
    amount: Optional[float] = Field(None, description="Budget amount as a numeric value")
    currency: str = Field("", description="Currency code, e.g. SAR, USD, EUR")

    @field_validator("amount", mode="before")
    @classmethod
    def coerce_amount(cls, v: Any) -> Optional[float]:
        if v is None or v == "" or v == "N/A":
            return None
        try:
            return float(str(v).replace(",", "").strip())
        except (ValueError, TypeError):
            return None

    @field_validator("currency", mode="before")
    @classmethod
    def clean_currency(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()


class ContactSchema(BaseModel):
    name: str = Field("", description="Contact person name")
    email: str = Field("", description="Contact email address")
    phone: str = Field("", description="Contact phone number")

    @field_validator("name", "email", "phone", mode="before")
    @classmethod
    def coerce_str(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()


class TenderSchema(BaseModel):
    title: str = Field("", description="Tender title")
    issuer: str = Field("", description="Issuing organisation")
    reference_number: str = Field("", description="Official reference / tender number")
    publication_date: Optional[str] = Field(None, description="Publication date (YYYY-MM-DD)")
    submission_deadline: Optional[str] = Field(None, description="Submission deadline (YYYY-MM-DD)")
    budget: BudgetSchema = Field(default_factory=BudgetSchema)
    scope_of_work: str = Field("", description="Description of work scope")
    key_requirements: list[str] = Field(default_factory=list)
    eligibility_criteria: list[str] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    contact: ContactSchema = Field(default_factory=ContactSchema)

    @field_validator(
        "title", "issuer", "reference_number", "scope_of_work", mode="before"
    )
    @classmethod
    def coerce_str(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator(
        "key_requirements",
        "eligibility_criteria",
        "evaluation_criteria",
        "deliverables",
        mode="before",
    )
    @classmethod
    def coerce_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item).strip() for item in v if item]
        return []

    @field_validator("publication_date", "submission_deadline", mode="before")
    @classmethod
    def normalise_date(cls, v: Any) -> Optional[str]:
        """Accept a variety of date strings; normalise to YYYY-MM-DD or None."""
        if v is None or v == "" or str(v).strip().upper() in ("N/A", "UNKNOWN", "NULL"):
            return None
        return _normalise_date_string(str(v).strip())

    @model_validator(mode="before")
    @classmethod
    def ensure_nested_defaults(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "budget" not in values or values["budget"] is None:
                values["budget"] = {}
            if "contact" not in values or values["contact"] is None:
                values["contact"] = {}
        return values


class LLMMetadataSchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    api_time: float = Field(0.0, description="LLM API call duration in seconds")
    input_tokens: int = Field(0, description="Number of prompt tokens consumed")
    output_tokens: int = Field(0, description="Number of completion tokens generated")
    model_name: str = Field("", description="Model identifier used for extraction")
    provider: str = Field("", description="LLM provider name (groq / openai)")

    @field_validator("api_time", mode="before")
    @classmethod
    def coerce_float(cls, v: Any) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    @field_validator("input_tokens", "output_tokens", mode="before")
    @classmethod
    def coerce_int(cls, v: Any) -> int:
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0


class TenderResponseSchema(BaseModel):
    request_id: str
    tender: TenderSchema = Field(default_factory=TenderSchema)
    llm_general_fields: LLMMetadataSchema = Field(default_factory=LLMMetadataSchema)


# ---------------------------------------------------------------------------
# Date normalisation helper
# ---------------------------------------------------------------------------

def _normalise_date_string(raw: str) -> Optional[str]:
    """Try to parse common date formats and return YYYY-MM-DD."""
    from datetime import datetime

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Return raw if we cannot parse — validator will not reject it
    return raw
