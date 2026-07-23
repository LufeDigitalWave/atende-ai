"""Tests for ExtractedLeadData schema (Phase 1 of v3 evolution)."""
import pytest
from pydantic import ValidationError

from app.schemas.lead_extraction import ExtractedField, ExtractedLeadData


class TestExtractedField:
    def test_string_value(self):
        f = ExtractedField(key="customer_name", value="Luiz", confidence=0.95)
        assert f.value == "Luiz"
        assert f.confidence == 0.95

    def test_int_value(self):
        f = ExtractedField(key="party_size", value=8, confidence=0.99)
        assert f.value == 8

    def test_confidence_validation(self):
        with pytest.raises(ValidationError):
            ExtractedField(key="x", value="y", confidence=1.5)
        with pytest.raises(ValidationError):
            ExtractedField(key="x", value="y", confidence=-0.1)


class TestExtractedLeadData:
    def test_minimal(self):
        d = ExtractedLeadData()
        assert d.detected_intent is None
        assert d.intent_confidence == 0.0
        assert d.extracted_fields == []
        assert d.should_handoff is False

    def test_full_extraction(self):
        d = ExtractedLeadData(
            detected_intent="reserva",
            intent_confidence=0.96,
            extracted_fields=[
                ExtractedField(key="reservation_date", value="sábado", confidence=0.9),
                ExtractedField(key="reservation_time", value="20:00", confidence=0.85),
                ExtractedField(key="party_size", value=8, confidence=0.99),
            ],
            should_handoff=False,
            lead_stage_suggestion="reservation_in_progress",
            notes=["Cliente demonstrou intenção clara de reserva."],
        )
        assert d.detected_intent == "reserva"
        assert len(d.extracted_fields) == 3

    def test_handoff_requires_reason(self):
        with pytest.raises(ValidationError):
            ExtractedLeadData(should_handoff=True, handoff_reason=None)

    def test_handoff_with_reason_ok(self):
        d = ExtractedLeadData(should_handoff=True, handoff_reason="Cliente pediu humano")
        assert d.should_handoff is True

    def test_get_field_value(self):
        d = ExtractedLeadData(
            extracted_fields=[
                ExtractedField(key="customer_name", value="Luiz", confidence=0.9),
            ]
        )
        assert d.get_field_value("customer_name") == "Luiz"
        assert d.get_field_value("nonexistent") is None

    def test_get_field_confidence(self):
        d = ExtractedLeadData(
            extracted_fields=[
                ExtractedField(key="customer_name", value="Luiz", confidence=0.9),
            ]
        )
        assert d.get_field_confidence("customer_name") == 0.9
        assert d.get_field_confidence("nonexistent") == 0.0


class TestLegacyMapping:
    def test_name_aliases(self):
        for key in ["customer_name", "name", "client_name"]:
            d = ExtractedLeadData(
                extracted_fields=[ExtractedField(key=key, value="Luiz", confidence=0.9)]
            )
            assert d.to_legacy_dict()["name"] == "Luiz"

    def test_service_aliases(self):
        for key in ["service_interest", "service", "tipo_servico", "produto"]:
            d = ExtractedLeadData(
                extracted_fields=[ExtractedField(key=key, value="almoço executivo", confidence=0.9)]
            )
            assert d.to_legacy_dict()["service_interest"] == "almoço executivo"

    def test_no_match_no_legacy(self):
        d = ExtractedLeadData(
            extracted_fields=[ExtractedField(key="party_size", value=8, confidence=0.9)]
        )
        assert d.to_legacy_dict() == {}

    def test_empty_extraction(self):
        assert ExtractedLeadData().to_legacy_dict() == {}
