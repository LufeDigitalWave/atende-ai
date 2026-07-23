"""Tests for Lead Scoring v3 (contextual by intent + journey)."""

from app.schemas.business_profile import (
    BusinessProfile,
    FAQItem,
    ObjectionItem,
    ServiceItem,
)
from app.schemas.conversation_profile import (
    ConversationJourney,
    ConversationProfile,
    QualificationField,
)
from app.schemas.lead_extraction import ExtractedField, ExtractedLeadData
from app.schemas.niche_profile import NicheProfile
from app.services.lead_scoring_v3 import (
    ScoreBreakdown,
    _default_points_for_field,
    _field_to_scoring_event,
    compute_score_legacy,
    compute_score_v3,
)


def _restaurant_profile() -> NicheProfile:
    business = BusinessProfile(
        agent_name="Mariana",
        company_name="Sabor da Terra",
        city="Curitiba",
        tagline="Culinária brasileira",
        services=[
            ServiceItem(name="Almoço", price_installments="1x R$ 49", price_cash="R$ 49", duration_or_scope="1h"),
            ServiceItem(name="Jantar", price_installments="1x R$ 79", price_cash="R$ 79", duration_or_scope="2h"),
            ServiceItem(name="Rodízio", price_installments="1x R$ 89", price_cash="R$ 89", duration_or_scope="2h"),
        ],
        qualification_extra_question="Qual cozinha?",
        faq=[FAQItem(q="xxxxx", a="xxxxx")] * 5,
        common_objections=[ObjectionItem(objection="xxxxx", guideline="xxxxxxxxxx")] * 3,
        tone_notes="amigável",
        opening_message="Oi! Sou a Mariana do Sabor da Terra",
        suggestions=["xxxxxxxxxx"] * 3,
    )
    conversation = ConversationProfile(
        business_mode="reservation_based",
        primary_intents=["cardapio", "reserva", "delivery", "horarios"],
        journeys=[
            ConversationJourney(
                intent="reserva",
                description="Reservar",
                response_goal="Confirmar",
                suggested_cta="Posso te ajudar",
                qualification_fields=["customer_name", "party_size", "reservation_date", "reservation_time"],
                handoff_conditions=["Cliente pede humano"],
                forbidden_questions=["Não perguntar orçamento"],
            ),
        ],
        qualification_fields=[
            QualificationField(key="customer_name", label="Nome", purpose="Personalizar atendimento"),
            QualificationField(key="party_size", label="Pessoas", purpose="Organizar mesa"),
            QualificationField(key="reservation_date", label="Data", purpose="Verificar disponibilidade"),
            QualificationField(key="reservation_time", label="Horário", purpose="Reservar slot"),
        ],
        recommended_ctas=[],
        prohibited_behaviors=["Não perguntar orçamento"],
        handoff_rules=["Cliente pede humano"],
        lead_scoring_rules={
            "intent_detected": 10,
            "name_informed": 10,
            "party_size_informed": 15,
            "date_informed": 15,
            "time_informed": 15,
        },
        proactive_opening_strategy="Apresentar",
        response_before_qualification=True,
        max_questions_per_message=1,
    )
    return NicheProfile(business=business, conversation=conversation)


class TestFieldToEvent:
    def test_customer_name(self):
        assert _field_to_scoring_event("customer_name", None) == "name_informed"

    def test_party_size(self):
        assert _field_to_scoring_event("party_size", None) == "party_size_informed"

    def test_unknown_field_returns_none(self):
        assert _field_to_scoring_event("unknown_field", None) is None


class TestDefaultPoints:
    def test_customer_name_default(self):
        assert _default_points_for_field("customer_name") == 10

    def test_party_size_default(self):
        assert _default_points_for_field("party_size") == 15

    def test_unknown_field_returns_10(self):
        assert _default_points_for_field("weird_field") == 10


class TestComputeScoreV3:
    def test_intent_only(self):
        ext = ExtractedLeadData(detected_intent="reserva", intent_confidence=0.9)
        score, breakdown = compute_score_v3(ext, _restaurant_profile())
        assert "intent_reserva" in breakdown
        assert breakdown["intent_reserva"] == 10
        assert score == 10

    def test_full_reservation_extract(self):
        """The exact scenario from the failed restaurante test."""
        ext = ExtractedLeadData(
            detected_intent="reserva",
            intent_confidence=0.96,
            extracted_fields=[
                ExtractedField(key="customer_name", value="Luiz", confidence=0.95),
                ExtractedField(key="party_size", value=8, confidence=0.9),
                ExtractedField(key="reservation_date", value="sábado", confidence=0.9),
                ExtractedField(key="reservation_time", value="20:00", confidence=0.9),
            ],
        )
        score, breakdown = compute_score_v3(ext, _restaurant_profile())
        # 10 (intent) + 10 (name) + 15 (party) + 15 (date) + 15 (time) + 30 (scheduling_confirmed) = 95
        assert score == 95
        assert breakdown["intent_reserva"] == 10
        assert breakdown["name_informed"] == 10
        assert breakdown["party_size_informed"] == 15
        assert breakdown["date_informed"] == 15
        assert breakdown["time_informed"] == 15
        assert breakdown["scheduling_confirmed"] == 30

    def test_score_capped_at_100(self):
        ext = ExtractedLeadData(
            detected_intent="reserva",
            intent_confidence=0.9,
            extracted_fields=[
                ExtractedField(key="customer_name", value="João", confidence=0.95),
                ExtractedField(key="party_size", value=4, confidence=0.9),
                ExtractedField(key="reservation_date", value="hoje", confidence=0.9),
                ExtractedField(key="reservation_time", value="20:00", confidence=0.9),
                # Extra fields that don't map to events
                ExtractedField(key="need_extra", value="x", confidence=0.5),
                ExtractedField(key="another_extra", value="y", confidence=0.5),
            ],
        )
        score, _ = compute_score_v3(ext, _restaurant_profile())
        assert score <= 100

    def test_empty_extraction_zero_score(self):
        ext = ExtractedLeadData()
        score, breakdown = compute_score_v3(ext, _restaurant_profile())
        assert score == 0
        assert breakdown.get("total", 0) == 0

    def test_field_with_null_value_ignored(self):
        ext = ExtractedLeadData(
            extracted_fields=[
                ExtractedField(key="customer_name", value=None, confidence=0.0),
            ]
        )
        score, breakdown = compute_score_v3(ext, _restaurant_profile())
        assert "name_informed" not in breakdown

    def test_handoff_does_not_score(self):
        """Handoff is a state transition, not a score."""
        ext = ExtractedLeadData(should_handoff=True, handoff_reason="Pediu humano")
        score, breakdown = compute_score_v3(ext, _restaurant_profile())
        assert score == 0
        assert "handoff" not in [k for k in breakdown if k != "total"]


class TestScoreBreakdown:
    def test_add_increments_total(self):
        b = ScoreBreakdown()
        b.add("test", 10)
        b.add("test2", 20)
        assert b.total == 30
        assert b.to_dict() == {"test": 10, "test2": 20, "total": 30}

    def test_to_dict_serialization(self):
        b = ScoreBreakdown()
        b.add("intent", 10)
        d = b.to_dict()
        assert "total" in d


class TestLegacyScoring:
    def test_legacy_still_works(self):
        """Make sure compute_score_legacy still functions for backward compat."""
        from app.models import BudgetRange, Urgency

        class MockLead:
            name = "João"
            service_interest = "almoço"
            complaint = "fome"
            budget_range = BudgetRange.ate_3k
            urgency = Urgency.alta
            score = 0
            state = None

        score, breakdown = compute_score_legacy(MockLead())
        # Should sum the legacy bonuses
        assert score > 0
        assert "name_filled" in breakdown
