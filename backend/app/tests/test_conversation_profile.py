"""Tests for ConversationProfile schema (Phase 1 of v3 evolution)."""
import pytest
from pydantic import ValidationError

from app.schemas.conversation_profile import (
    BusinessMode,
    ConversationJourney,
    ConversationProfile,
    QualificationField,
)


class TestQualificationField:
    def test_minimal_field(self):
        f = QualificationField(
            key="customer_name", label="Nome", purpose="Personalizar atendimento"
        )
        assert f.priority == "medium"
        assert f.ask_only_when_relevant is True

    def test_with_required_for(self):
        f = QualificationField(
            key="party_size",
            label="Quantidade de pessoas",
            purpose="Organizar mesa",
            required_for=["reserva", "evento_grupo"],
            priority="high",
            ask_only_when_relevant=True,
        )
        assert f.priority == "high"
        assert "reserva" in f.required_for

    def test_key_too_short_rejected(self):
        with pytest.raises(ValidationError):
            QualificationField(key="x", label="Nome", purpose="X")

    def test_invalid_priority_rejected(self):
        with pytest.raises(ValidationError):
            QualificationField(
                key="customer_name", label="Nome",
                purpose="X", priority="urgent",
            )


class TestConversationJourney:
    def test_minimal_journey(self):
        j = ConversationJourney(
            intent="reserva",
            description="Reservar mesa",
            response_goal="Confirmar reserva",
            suggested_cta="Posso verificar disponibilidade.",
        )
        assert j.intent == "reserva"
        assert j.qualification_fields == []
        assert j.forbidden_questions == []

    def test_full_journey(self):
        j = ConversationJourney(
            intent="reserva",
            description="Reservar mesa",
            response_goal="Confirmar reserva com data/horario/pessoas",
            suggested_cta="Posso te ajudar com a reserva.",
            qualification_fields=["customer_name", "party_size", "reservation_date"],
            handoff_conditions=["date + party_size informados"],
            forbidden_questions=["Não perguntar faixa de investimento"],
        )
        assert len(j.qualification_fields) == 3


class TestConversationProfile:
    def test_minimal_restaurant_profile(self):
        p = ConversationProfile(
            business_mode="reservation_based",
            primary_intents=["cardapio", "reserva", "delivery", "horarios"],
            journeys=[
                ConversationJourney(
                    intent="reserva",
                    description="Reservar mesa",
                    response_goal="Confirmar reserva",
                    suggested_cta="Posso te ajudar com a reserva.",
                )
            ],
            qualification_fields=[
                QualificationField(
                    key="customer_name", label="Nome",
                    purpose="Personalizar reserva",
                )
            ],
            prohibited_behaviors=["Não perguntar orçamento para almoço"],
            handoff_rules=["Cliente pede humano"],
            proactive_opening_strategy="Apresentar valor principal e oferecer caminhos.",
        )
        assert p.business_mode == "reservation_based"
        assert p.response_before_qualification is True
        assert p.max_questions_per_message == 1

    def test_primary_intents_count_validation(self):
        # Too few intents
        with pytest.raises(ValidationError):
            ConversationProfile(
                business_mode="reservation_based",
                primary_intents=["only_one"],
                journeys=[
                    ConversationJourney(
                        intent="reserva",
                        description="XXXXX",
                        response_goal="XXXXX",
                        suggested_cta="XXXXX",
                    )
                ],
                qualification_fields=[
                    QualificationField(key="customer_name", label="Nome", purpose="XXXXX")
                ],
                prohibited_behaviors=["XXXXX"],
                handoff_rules=["XXXXX"],
                proactive_opening_strategy="XXXXXXXXXX",
            )

    def test_prohibited_behaviors_required(self):
        with pytest.raises(ValidationError):
            ConversationProfile(
                business_mode="reservation_based",
                primary_intents=["a", "b", "c"],
                journeys=[
                    ConversationJourney(
                        intent="reserva",
                        description="XXXXX",
                        response_goal="XXXXX",
                        suggested_cta="XXXXX",
                    )
                ],
                qualification_fields=[
                    QualificationField(key="customer_name", label="Nome", purpose="XXXXX")
                ],
                prohibited_behaviors=[],
                handoff_rules=["XXXXX"],
                proactive_opening_strategy="XXXXXXXXXX",
            )

    def test_max_questions_per_message(self):
        with pytest.raises(ValidationError):
            ConversationProfile(
                business_mode="reservation_based",
                primary_intents=["a", "b", "c"],
                journeys=[
                    ConversationJourney(
                        intent="reserva",
                        description="XXXXX",
                        response_goal="XXXXX",
                        suggested_cta="XXXXX",
                    )
                ],
                qualification_fields=[
                    QualificationField(key="customer_name", label="Nome", purpose="XXXXX")
                ],
                prohibited_behaviors=["XXXXX"],
                handoff_rules=["XXXXX"],
                proactive_opening_strategy="XXXXXXXXXX",
                max_questions_per_message=5,
            )


class TestBusinessMode:
    @pytest.mark.parametrize("mode", [
        "transactional", "appointment_based", "reservation_based",
        "consultative", "mixed",
    ])
    def test_all_modes_valid(self, mode):
        # Build the minimum required profile with each mode
        p = ConversationProfile(
            business_mode=mode,
            primary_intents=["a", "b", "c"],
            journeys=[
                ConversationJourney(
                    intent="xx",
                    description="XXXXX",
                    response_goal="XXXXX",
                    suggested_cta="XXXXX",
                )
            ],
            qualification_fields=[
                QualificationField(key="customer_name", label="Nome", purpose="XXXXX")
            ],
            prohibited_behaviors=["XXXXX"],
            handoff_rules=["XXXXX"],
            proactive_opening_strategy="XXXXXXXXXX",
        )
        assert p.business_mode == mode