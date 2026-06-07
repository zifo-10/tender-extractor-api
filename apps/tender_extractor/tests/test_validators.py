"""Tests for LLMJSONValidator."""
import pytest

from apps.tender_extractor.schemas import TenderSchema
from apps.tender_extractor.validators import LLMJSONValidator


@pytest.fixture
def validator():
    return LLMJSONValidator()


class TestLLMJSONValidator:
    def test_valid_dict(self, validator):
        data = {
            "title": "Test Tender",
            "issuer": "Ministry",
            "key_requirements": ["req1", "req2"],
        }
        result = validator.validate_and_normalise(data)
        assert isinstance(result, TenderSchema)
        assert result.title == "Test Tender"

    def test_unknown_fields_stripped(self, validator):
        data = {"title": "T", "unknown_field": "should_be_stripped"}
        result = validator.validate_and_normalise(data)
        assert not hasattr(result, "unknown_field")

    def test_null_input_returns_default(self, validator):
        result = validator.validate_and_normalise(None)
        assert isinstance(result, TenderSchema)
        assert result.title == ""

    def test_arrays_defaulted_from_none(self, validator):
        data = {"key_requirements": None, "deliverables": None}
        result = validator.validate_and_normalise(data)
        assert result.key_requirements == []
        assert result.deliverables == []

    def test_string_array_split(self, validator):
        data = {"key_requirements": "req1\nreq2\nreq3"}
        result = validator.validate_and_normalise(data)
        assert len(result.key_requirements) == 3

    def test_broken_budget_repaired(self, validator):
        data = {"budget": "not-a-dict"}
        result = validator.validate_and_normalise(data)
        assert result.budget.amount is None

    def test_broken_contact_repaired(self, validator):
        data = {"contact": 12345}
        result = validator.validate_and_normalise(data)
        assert result.contact.name == ""

    def test_full_valid_payload(self, validator):
        data = {
            "title": "IT Equipment Supply",
            "issuer": "MOF",
            "reference_number": "MOF-001",
            "publication_date": "2024-01-01",
            "submission_deadline": "2024-02-01",
            "budget": {"amount": 100000, "currency": "SAR"},
            "scope_of_work": "Supply laptops",
            "key_requirements": ["certified"],
            "eligibility_criteria": ["registered"],
            "evaluation_criteria": ["price"],
            "deliverables": ["laptops"],
            "contact": {"name": "Ali", "email": "ali@mof.sa", "phone": "+966"},
        }
        result = validator.validate_and_normalise(data)
        assert result.title == "IT Equipment Supply"
        assert result.budget.amount == 100000.0
        assert result.contact.name == "Ali"
