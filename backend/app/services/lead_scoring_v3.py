"""Lead scoring v3 — contextual by intent + journey.

Uses ConversationProfile.lead_scoring_rules and ConversationJourney rules to
compute a score that's contextual to the niche — NOT universal 5-field score.

Per-niche scoring examples:
- Restaurante: intent_detected=+10, party_size_informed=+15,
  date_informed=+15, time_informed=+15, name_informed=+10,
  reservation_complete=+25, ask_for_human=handoff
- Clínica: need_detected=+20, urgency_high=+15, availability=+15,
  all_qualification_fields=+25, ask_for_human=handoff

Fallback to legacy scoring if no profile provided (for backward compat).
"""
from __future__ import annotations

from typing import Any

from app.schemas.conversation_profile import ConversationProfile
from app.schemas.lead_extraction import ExtractedLeadData
from app.schemas.niche_profile import NicheProfile
from app.services.lead_extractor import ExtractedField


class ScoreBreakdown:
    """Explainable score breakdown."""

    def __init__(self):
        self.components: dict[str, int] = {}
        self.total = 0

    def add(self, key: str, points: int) -> None:
        self.components[key] = points
        self.total += points

    def to_dict(self) -> dict[str, int]:
        return {**self.components, "total": self.total}


def compute_score_v3(
    extraction: ExtractedLeadData,
    profile: NicheProfile,
) -> tuple[int, dict[str, int]]:
    """Compute lead score using ConversationProfile rules.

    Returns (score, breakdown). Score is capped at 100.
    """
    breakdown = ScoreBreakdown()
    conv = profile.conversation

    # 1. Intent detected (small bonus)
    if extraction.detected_intent:
        intent_points = conv.lead_scoring_rules.get("intent_detected", 10)
        breakdown.add(f"intent_{extraction.detected_intent}", intent_points)

    # 2. Per-field scoring from extracted fields
    for ef in extraction.extracted_fields:
        if ef.value is None:
            continue

        # Map field key to scoring event
        scoring_event = _field_to_scoring_event(ef.key, conv)
        if scoring_event is None:
            continue

        points = conv.lead_scoring_rules.get(scoring_event, _default_points_for_field(ef.key))
        breakdown.add(scoring_event, points)

    # 3. Bonus: scheduling confirmed (date + time both present = strong qualification signal)
    has_date = any(ef.key in ("reservation_date", "availability", "scheduled_date") and ef.value for ef in extraction.extracted_fields)
    has_time = any(ef.key in ("reservation_time", "scheduled_time") and ef.value for ef in extraction.extracted_fields)
    if has_date and has_time:
        bonus = conv.lead_scoring_rules.get("scheduling_confirmed", 30)
        breakdown.add("scheduling_confirmed", bonus)

    # 4. Bonus: service interest expressed (mapped from various keys)
    has_service = any(ef.key in ("service_interest", "product_interest", "need", "course_interest") and ef.value for ef in extraction.extracted_fields)
    if has_service and "service_expressed" not in breakdown.to_dict():
        bonus = conv.lead_scoring_rules.get("service_expressed", 20)
        breakdown.add("service_expressed", bonus)

    # 5. Cap at 100
    final_score = min(breakdown.total, 100)
    return final_score, breakdown.to_dict()


def _field_to_scoring_event(key: str, conv: ConversationProfile) -> str | None:
    """Map extracted field key to a scoring event name (or None to skip)."""
    mapping = {
        "customer_name": "name_informed",
        "name": "name_informed",
        "client_name": "name_informed",
        "party_size": "party_size_informed",
        "reservation_date": "date_informed",
        "reservation_time": "time_informed",
        "scheduled_date": "date_informed",
        "scheduled_time": "time_informed",
        "need": "need_informed",
        "urgency": "urgency_informed",
        "availability": "availability_informed",
        "problem_type": "problem_informed",
        "decision_maker": "decision_maker_informed",
        "product_interest": "product_informed",
        "service_interest": "service_informed",
        "course_interest": "service_informed",
        "delivery_zone": "delivery_zone_informed",
        "payment_preference": "payment_informed",
    }
    return mapping.get(key)


def _default_points_for_field(key: str) -> int:
    """Default scoring points for a field (when not in profile.lead_scoring_rules)."""
    defaults = {
        "customer_name": 10,
        "party_size": 15,
        "reservation_date": 15,
        "reservation_time": 15,
        "scheduled_date": 15,
        "scheduled_time": 15,
        "need": 20,
        "urgency": 15,
        "availability": 15,
        "problem_type": 15,
        "decision_maker": 20,
        "product_interest": 15,
        "service_interest": 20,
        "course_interest": 20,
        "delivery_zone": 10,
        "payment_preference": 10,
    }
    return defaults.get(key, 10)


# ============================================================
# Legacy scoring (preserved for backward compat)
# ============================================================

def compute_score_legacy(lead) -> tuple[int, dict[str, int]]:
    """Original 5-field scoring (used when no profile available)."""
    from app.models import BudgetRange, Urgency

    breakdown = ScoreBreakdown()

    if lead.name and lead.name.strip():
        breakdown.add("name_filled", 20)
    if lead.service_interest and lead.service_interest.strip():
        breakdown.add("service_interest_filled", 20)
    if lead.complaint and lead.complaint.strip():
        breakdown.add("complaint_filled", 15)
    if lead.budget_range != BudgetRange.nao_informado:
        breakdown.add("budget_range_set", 20)
        if lead.budget_range in [BudgetRange.ate_3k, BudgetRange.ate_6k, BudgetRange.acima_6k]:
            breakdown.add("budget_mid_or_high", 10)
    if lead.urgency != Urgency.nao_informada:
        breakdown.add("urgency_set", 15)
        if lead.urgency == Urgency.alta:
            breakdown.add("urgency_alta", 10)

    return min(breakdown.total, 100), breakdown.to_dict()