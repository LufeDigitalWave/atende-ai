"""Lead extraction schema — what the LLM-extractor returns per turn.

Replaces the heuristic extractor. The extractor LLM:
- Receives the schema of allowed fields (from ConversationProfile.qualification_fields)
- Returns ONLY ExtractedLeadData fields, validated by Pydantic
- Includes confidence per field to prevent overwriting confirmed data

This is data, not behavior — the extractor is deterministic in shape, dynamic in content.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ExtractedField(BaseModel):
    """A single field extraction result."""

    key: str = Field(..., min_length=2, max_length=60)
    value: str | int | float | bool | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractedLeadData(BaseModel):
    """Result of one extraction turn.

    Returned by the extractor LLM via tool use / JSON mode.
    Validated against the ConversationProfile allowed fields.
    """

    detected_intent: str | None = Field(
        default=None, max_length=60,
        description="Which intent was detected (matches ConversationProfile.primary_intents)"
    )
    intent_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How confident the extractor is about the detected intent"
    )

    extracted_fields: list[ExtractedField] = Field(
        default_factory=list,
        description="Fields extracted from this turn (only fields allowed by ConversationProfile)"
    )

    should_handoff: bool = False
    handoff_reason: str | None = Field(
        default=None, max_length=200,
        description="If should_handoff is True, why (e.g., 'Cliente pediu humano', 'Reserva completa')"
    )

    lead_stage_suggestion: str | None = Field(
        default=None, max_length=60,
        description="What state the lead should move to (e.g., 'novo', 'em_qualificacao', 'handoff')"
    )

    notes: list[str] = Field(
        default_factory=list, max_length=5,
        description="Free-form observations about the turn (for debugging, never shown to visitor)"
    )

    @model_validator(mode="after")
    def validate_handoff_pair(self):
        if self.should_handoff and not self.handoff_reason:
            raise ValueError("handoff_reason is required when should_handoff is True")
        return self

    def get_field_value(self, key: str) -> Any | None:
        """Get value of an extracted field by key (or None)."""
        for ef in self.extracted_fields:
            if ef.key == key:
                return ef.value
        return None

    def get_field_confidence(self, key: str) -> float:
        """Get confidence of an extracted field (or 0.0)."""
        for ef in self.extracted_fields:
            if ef.key == key:
                return ef.confidence
        return 0.0

    def to_legacy_dict(self) -> dict[str, Any]:
        """Map extracted_fields back to the legacy Lead columns (name, service_interest, etc)
        for backward compatibility with the existing frontend SSE schema.

        Mapping rules:
        - 'customer_name' / 'name' -> name
        - 'service_interest' / 'service' -> service_interest
        - 'complaint' / 'need' -> complaint
        - 'budget' / 'budget_range' -> budget_range
        - 'urgency' -> urgency
        """
        legacy: dict[str, Any] = {}
        for ef in self.extracted_fields:
            if ef.key in ("customer_name", "name", "client_name", "visitante"):
                legacy["name"] = ef.value
            elif ef.key in ("service_interest", "service", "tipo_servico", "produto"):
                legacy["service_interest"] = ef.value
            elif ef.key in ("complaint", "need", "necessidade", "objetivo"):
                legacy["complaint"] = ef.value
            elif ef.key in ("budget", "budget_range", "orcamento", "investimento"):
                legacy["budget_range"] = ef.value
            elif ef.key in ("urgency", "urgencia"):
                legacy["urgency"] = ef.value
        return legacy