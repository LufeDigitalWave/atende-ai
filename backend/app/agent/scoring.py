"""Lead scoring — deterministic, explainable, code-based (not LLM)."""
from __future__ import annotations

from app.models import BudgetRange, Lead, Urgency


MIN_BUDGET_TICKET = 1000  # R$ 1.000 mínimo pro bonus
MIN_BUDGET_RANGE = BudgetRange.ate_3k  # ate_3k = ate 3 mil


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


def compute_score(lead: Lead) -> tuple[int, dict[str, int]]:
    """
    Compute lead score (0–100) based on fields + budget + urgency.

    **Scoring rules:**
    - Name filled: +20
    - Service interest filled: +20
    - Complaint filled: +15
    - Budget range set (not nao_informado): +20
      - Bonus if ate_3k or higher: +10
    - Urgency set (not nao_informada): +15
      - Bonus if alta: +10

    Max: 20+20+15+20+10+15+10 = 110 (capped at 100)
    """
    breakdown = ScoreBreakdown()

    # 1. Name (20 points)
    if lead.name and lead.name.strip():
        breakdown.add("name_filled", 20)

    # 2. Service interest (20 points)
    if lead.service_interest and lead.service_interest.strip():
        breakdown.add("service_interest_filled", 20)

    # 3. Complaint (15 points)
    if lead.complaint and lead.complaint.strip():
        breakdown.add("complaint_filled", 15)

    # 4. Budget (20 + potential 10 bonus)
    if lead.budget_range != BudgetRange.nao_informado:
        breakdown.add("budget_range_set", 20)
        # Bonus if mid-range or higher
        if lead.budget_range in [BudgetRange.ate_3k, BudgetRange.ate_6k, BudgetRange.acima_6k]:
            breakdown.add("budget_mid_or_high", 10)

    # 5. Urgency (15 + potential 10 bonus)
    if lead.urgency != Urgency.nao_informada:
        breakdown.add("urgency_set", 15)
        # Bonus if alta
        if lead.urgency == Urgency.alta:
            breakdown.add("urgency_alta", 10)

    # Cap at 100
    final_score = min(breakdown.total, 100)

    return final_score, breakdown.to_dict()
