"""Conversation profile schema — describes how the agent should behave per niche.

Separates:
- WHAT data the agent has (BusinessProfile: services, FAQ, prices) — what to say
- HOW it should behave (ConversationProfile: intents, journeys, qualification rules) — how to say

This is data, never instructions. The agent template renders this into a system prompt.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ============================================================
# Enums (allowed values)
# ============================================================

BusinessMode = Literal[
    "transactional",        # venda direta (e-commerce, delivery)
    "appointment_based",    # agendamento (clínica, salão)
    "reservation_based",    # reserva (restaurante, hotel)
    "consultative",         # consultivo (B2B, imobiliária, advocacia)
    "mixed",                # misto (academia, loja física)
]

FieldPriority = Literal["high", "medium", "low"]


# ============================================================
# Building blocks
# ============================================================

class QualificationField(BaseModel):
    """A field that may be collected during the conversation."""

    key: str = Field(
        ..., min_length=2, max_length=60,
        description="Internal identifier (e.g., 'customer_name', 'party_size')"
    )
    label: str = Field(
        ..., min_length=2, max_length=80,
        description="Human-readable label (e.g., 'Quantidade de pessoas')"
    )
    purpose: str = Field(
        ..., min_length=5, max_length=200,
        description="Why this field is useful — helps the agent decide when to ask"
    )
    required_for: list[str] = Field(
        default_factory=list,
        description="Which intents/journeys this field is required for (e.g., ['reserva'])"
    )
    priority: FieldPriority = "medium"
    ask_only_when_relevant: bool = True
    prohibited_before_intent: bool = False


class ConversationJourney(BaseModel):
    """One flow the agent can guide the visitor through."""

    intent: str = Field(
        ..., min_length=2, max_length=60,
        description="Intent identifier (e.g., 'reserva', 'cardapio', 'avaliacao')"
    )
    description: str = Field(
        ..., min_length=5, max_length=200,
        description="What this journey is about"
    )
    response_goal: str = Field(
        ..., min_length=5, max_length=200,
        description="What the agent must achieve for this journey"
    )
    suggested_cta: str = Field(
        ..., min_length=5, max_length=200,
        description="Example of an appropriate CTA for this journey"
    )
    qualification_fields: list[str] = Field(
        default_factory=list,
        description="Which QualificationField.keys are useful for this journey"
    )
    handoff_conditions: list[str] = Field(
        default_factory=list,
        description="When to hand off during this journey (e.g., 'date + party_size informed')"
    )
    forbidden_questions: list[str] = Field(
        default_factory=list,
        description="Questions the agent MUST NOT ask in this journey"
    )


class JourneyQuestion(BaseModel):
    """A single FAQ entry."""

    q: str = Field(..., min_length=5, max_length=200)
    a: str = Field(..., min_length=5, max_length=400)


class ConversationProfile(BaseModel):
    """How the agent should behave in a niche.

    Associated with a BusinessProfile. Describes the conversational logic:
    journey types, qualification strategy, what not to ask, when to handoff.
    """

    business_mode: BusinessMode

    primary_intents: list[str] = Field(
        ..., min_length=3, max_length=8,
        description="Common visitor intents in this niche"
    )

    journeys: list[ConversationJourney] = Field(
        ..., min_length=1, max_length=6,
        description="The main conversational flows the agent guides"
    )

    qualification_fields: list[QualificationField] = Field(
        ..., min_length=1, max_length=10,
        description="Fields that may be collected, with rules about when"
    )

    recommended_ctas: list[str] = Field(
        default_factory=list,
        description="Templates of CTAs appropriate for this business_mode"
    )

    prohibited_behaviors: list[str] = Field(
        ..., min_length=1, max_length=8,
        description="Things the agent MUST NOT do in this niche"
    )

    handoff_rules: list[str] = Field(
        ..., min_length=1, max_length=6,
        description="Conditions that trigger handoff to a human"
    )

    lead_scoring_rules: dict[str, int] = Field(
        default_factory=dict,
        description="Optional per-intent/event score increments (e.g., {'intent_detected': 5, 'date_informed': 15})"
    )

    proactive_opening_strategy: str = Field(
        ..., min_length=10, max_length=400,
        description="How the agent should open the conversation when visitor sends generic greeting"
    )

    response_before_qualification: bool = True
    """When True, agent must answer the visitor's question BEFORE asking for data."""

    max_questions_per_message: int = Field(
        default=1, ge=1, le=2,
        description="Maximum questions in a single agent message (1 recommended)"
    )
