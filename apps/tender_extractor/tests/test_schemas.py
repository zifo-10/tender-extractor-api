"""Tests for Pydantic schemas."""
import pytest

from apps.tender_extractor.schemas import (
    BudgetSchema,
    ContactSchema,
    TenderSchema,
    LLMMetadataSchema,
    TenderResponseSchema,
)


class TestBudgetSchema:
    def test_valid_budget(self):
        b = BudgetSchema(amount=500000.0, currency="SAR")
        assert b.amount == 500000.0
        assert b.currency == "SAR"

    def test_amount_coerced_from_string(self):
        b = BudgetSchema(amount="1,000,000.50", currency="USD")
        assert b.amount == 1_000_000.50

    def test_null_amount_string(self):
        b = BudgetSchema(amount="N/A", currency="")
        assert b.amount is None

    def test_defaults(self):
        b = BudgetSchema()
        assert b.amount is None
        assert b.currency == ""


class TestContactSchema:
    def test_valid_contact(self):
        c = ContactSchema(name="Ahmed", email="a@b.com", phone="+966")
        assert c.name == "Ahmed"
        assert c.email == "a@b.com"

    def test_none_fields_default_to_empty_string(self):
        c = ContactSchema(name=None, email=None, phone=None)
        assert c.name == ""
        assert c.email == ""
        assert c.phone == ""


class TestTenderSchema:
    def test_defaults(self):
        t = TenderSchema()
        assert t.title == ""
        assert t.key_requirements == []
        assert t.budget.amount is None

    def test_date_normalisation_slash(self):
        t = TenderSchema(publication_date="15/06/2024")
        assert t.publication_date == "2024-06-15"

    def test_date_normalisation_iso(self):
        t = TenderSchema(submission_deadline="2024-12-31")
        assert t.submission_deadline == "2024-12-31"

    def test_null_date(self):
        t = TenderSchema(publication_date=None)
        assert t.publication_date is None

    def test_na_date_becomes_none(self):
        t = TenderSchema(publication_date="N/A")
        assert t.publication_date is None

    def test_array_fields_coerced(self):
        t = TenderSchema(key_requirements=None)
        assert t.key_requirements == []

    def test_nested_defaults_on_missing_budget(self):
        data = {"title": "Test Tender"}
        t = TenderSchema(**data)
        assert t.budget.amount is None
        assert t.budget.currency == ""


class TestLLMMetadataSchema:
    def test_defaults(self):
        m = LLMMetadataSchema()
        assert m.api_time == 0.0
        assert m.input_tokens == 0
        assert m.output_tokens == 0
        assert m.model_name == ""

    def test_coerce_string_tokens(self):
        m = LLMMetadataSchema(input_tokens="100", output_tokens="50")
        assert m.input_tokens == 100
        assert m.output_tokens == 50


class TestTenderResponseSchema:
    def test_full_response(self):
        r = TenderResponseSchema(
            request_id="req-001",
            tender=TenderSchema(title="Test"),
            llm_general_fields=LLMMetadataSchema(model_name="gpt-4"),
        )
        assert r.request_id == "req-001"
        assert r.tender.title == "Test"
        assert r.llm_general_fields.model_name == "gpt-4"
