"""Parallel extraction of lead fields from message + response."""
from __future__ import annotations

import json
import re
from typing import Any

from app.models import BudgetRange, Lead, Urgency


class ExtractionResult:
    """Extracted fields."""

    def __init__(
        self,
        name: str | None = None,
        service_interest: str | None = None,
        complaint: str | None = None,
        budget_range: BudgetRange | None = None,
        urgency: Urgency | None = None,
    ):
        self.name = name
        self.service_interest = service_interest
        self.complaint = complaint
        self.budget_range = budget_range
        self.urgency = urgency

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "service_interest": self.service_interest,
            "complaint": self.complaint,
            "budget_range": self.budget_range.value if self.budget_range else None,
            "urgency": self.urgency.value if self.urgency else None,
        }


def extract_fields(
    user_message: str, agent_response: str, current_lead: Lead
) -> ExtractionResult:
    """
    Extract lead fields from user message + agent response.

    **Heuristics:**
    - Name: "meu nome é X", "eu sou X", "chamo X"
    - Service: "melasma", "acne", "depilação", "limpeza", etc (keywords from base)
    - Complaint: "manchas", "cicatrizes", "queda de cabelo", etc
    - Budget: "posso gastar", "meu orçamento", numbers (1k, 2k, 3k, 5k, etc)
    - Urgency: "urgente", "logo", "já", "amanhã" (alta); "quando possível" (baixa)

    Conservative: only extract when confident.
    """
    text = (user_message + " " + agent_response).lower()
    result = ExtractionResult()

    # 1. Name patterns
    patterns = [
        r"meu nome [eé] ([a-záéíóúàâãõç]+)",
        r"eu sou ([a-záéíóúàâãõç]+)",
        r"chamo ([a-záéíóúàâãõç]+)",
        r"sou ([a-záéíóúàâãõç]{3,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result.name = match.group(1).capitalize()
            break

    # 2. Service interest (hardcoded keywords from base)
    services = [
        "melasma",
        "acne",
        "depilação",
        "limpeza",
        "peeling",
        "microagulhamento",
        "botox",
        "preenchimento",
        "criolipólise",
        "radiofrequência",
        "drenagem",
        "cabelo",
    ]
    for service in services:
        if service in text:
            result.service_interest = service
            break

    # 3. Complaint (keywords)
    complaints = [
        "manchas",
        "cicatrizes",
        "acne",
        "rugas",
        "flacidez",
        "queda",
        "oleosidade",
        "ressecamento",
    ]
    for complaint in complaints:
        if complaint in text:
            result.complaint = complaint
            break

    # 4. Budget range (extract numbers + compare)
    budget_keywords = {
        BudgetRange.ate_1k: ["até 1", "1 mil", "mil reais", "1000"],
        BudgetRange.ate_3k: ["até 3", "3 mil", "3000", "2 mil", "2000"],
        BudgetRange.ate_6k: ["até 6", "6 mil", "6000", "4 mil", "4000", "5 mil"],
        BudgetRange.acima_6k: ["acima de 6", "mais de 6", "10 mil", "10000", "8 mil"],
    }
    for budget_range, keywords in budget_keywords.items():
        for kw in keywords:
            if kw in text:
                result.budget_range = budget_range
                break
        if result.budget_range:
            break

    # 5. Urgency
    if any(w in text for w in ["urgente", "logo", "amanhã", "hoje", "agora", "já", "rápido"]):
        result.urgency = Urgency.alta
    elif any(w in text for w in ["quando possível", "sem pressa", "aos poucos", "sem urgência"]):
        result.urgency = Urgency.baixa
    elif any(w in text for w in ["próxima semana", "em breve", "semana que vem"]):
        result.urgency = Urgency.media

    return result


def apply_extraction(lead: Lead, extraction: ExtractionResult) -> bool:
    """
    Apply extraction to lead, only updating if new data provided.
    Returns True if anything changed.
    """
    changed = False

    if extraction.name and not lead.name:
        lead.name = extraction.name
        changed = True
    if extraction.service_interest and not lead.service_interest:
        lead.service_interest = extraction.service_interest
        changed = True
    if extraction.complaint and not lead.complaint:
        lead.complaint = extraction.complaint
        changed = True
    if (
        extraction.budget_range
        and lead.budget_range == BudgetRange.nao_informado
    ):
        lead.budget_range = extraction.budget_range
        changed = True
    if extraction.urgency and lead.urgency == Urgency.nao_informada:
        lead.urgency = extraction.urgency
        changed = True

    return changed
