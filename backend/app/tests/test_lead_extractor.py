"""Tests for LLM-based Lead Extractor (Phase 4 of v3 evolution)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
from app.schemas.niche_profile import NicheProfile
from app.services.lead_extractor import (
    _build_extraction_prompt,
    _heuristic_fallback,
    extract_lead_data,
)


def _restaurant_profile() -> NicheProfile:
    business = BusinessProfile(
        agent_name="Mariana",
        company_name="Sabor da Terra",
        city="Curitiba",
        tagline="Culinária brasileira regional",
        services=[
            ServiceItem(name="Almoço", price_installments="1x R$ 49", price_cash="R$ 49", duration_or_scope="1h"),
            ServiceItem(name="Jantar", price_installments="1x R$ 79", price_cash="R$ 79", duration_or_scope="2h"),
            ServiceItem(name="Rodízio", price_installments="1x R$ 89", price_cash="R$ 89", duration_or_scope="2h"),
        ],
        qualification_extra_question="Qual tipo de cozinha?",
        faq=[FAQItem(q="xxxxx", a="xxxxx")] * 5,
        common_objections=[ObjectionItem(objection="xxxxx", guideline="xxxxxxxxxx")] * 3,
        tone_notes="amigável",
        opening_message="Oi! Sou a Mariana",
        suggestions=["xxxxxxxxxx"] * 3,
    )
    conversation = ConversationProfile(
        business_mode="reservation_based",
        primary_intents=["cardapio", "reserva", "delivery", "horarios"],
        journeys=[
            ConversationJourney(
                intent="reserva",
                description="Reservar mesa",
                response_goal="Confirmar reserva",
                suggested_cta="Posso te ajudar.",
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
        proactive_opening_strategy="Apresentar opções",
        response_before_qualification=True,
        max_questions_per_message=1,
    )
    return NicheProfile(business=business, conversation=conversation)


class TestHeuristicFallback:
    def test_name_with_prefix(self):
        profile = _restaurant_profile()
        result = _heuristic_fallback(
            "Meu nome é João",
            "Prazer, João!",
            profile,
        )
        name_field = next((f for f in result.extracted_fields if f.key == "customer_name"), None)
        assert name_field is not None
        assert name_field.value == "João"

    def test_name_repeated_by_agent(self):
        profile = _restaurant_profile()
        result = _heuristic_fallback(
            "Luiz",
            "Obrigada, Luiz! Vou te conectar.",
            profile,
        )
        name_field = next((f for f in result.extracted_fields if f.key == "customer_name"), None)
        assert name_field is not None
        assert name_field.value == "Luiz"

    def test_party_size(self):
        profile = _restaurant_profile()
        result = _heuristic_fallback(
            "Somos 8 pessoas",
            "Ótimo! Para que horas?",
            profile,
        )
        ps_field = next((f for f in result.extracted_fields if f.key == "party_size"), None)
        assert ps_field is not None
        assert ps_field.value == 8

    def test_reservation_date_hoje(self):
        profile = _restaurant_profile()
        result = _heuristic_fallback(
            "Quero almoçar hoje",
            "Para que horas?",
            profile,
        )
        date_field = next((f for f in result.extracted_fields if f.key == "reservation_date"), None)
        assert date_field is not None
        assert date_field.value == "hoje"

    def test_reservation_time(self):
        profile = _restaurant_profile()
        result = _heuristic_fallback(
            "Para as 20h",
            "Ótimo!",
            profile,
        )
        time_field = next((f for f in result.extracted_fields if f.key == "reservation_time"), None)
        assert time_field is not None
        assert time_field.value == "20:00"

    def test_handoff_atendente(self):
        profile = _restaurant_profile()
        result = _heuristic_fallback(
            "Quero falar com um atendente",
            "Vou transferir.",
            profile,
        )
        assert result.should_handoff is True
        assert result.handoff_reason is not None

    def test_handoff_humano(self):
        profile = _restaurant_profile()
        result = _heuristic_fallback(
            "Preciso de um humano",
            "...",
            profile,
        )
        assert result.should_handoff is True

    def test_intent_detection(self):
        profile = _restaurant_profile()
        result = _heuristic_fallback(
            "Quero fazer uma reserva para sábado",
            "...",
            profile,
        )
        assert result.detected_intent == "reserva"

    def test_no_intent_in_greeting(self):
        profile = _restaurant_profile()
        result = _heuristic_fallback(
            "Oi",
            "Olá!",
            profile,
        )
        assert result.detected_intent is None

    def test_extracts_from_full_restaurant_turn(self):
        """The exact scenario from the failed E2E test (restaurante)."""
        profile = _restaurant_profile()
        result = _heuristic_fallback(
            "Quero reservar para sábado à noite, somos 8 pessoas às 20h, meu nome é Luiz",
            "Perfeito, Luiz! Vou encaminhar a reserva.",
            profile,
        )
        keys = {f.key for f in result.extracted_fields}
        assert "customer_name" in keys
        assert "party_size" in keys
        assert "reservation_time" in keys


class TestExtractionPrompt:
    def test_prompt_contains_intents(self):
        p = _restaurant_profile()
        prompt = _build_extraction_prompt(
            "oi", "Olá!", p
        )
        assert "cardapio" in prompt
        assert "reserva" in prompt

    def test_prompt_contains_allowed_keys(self):
        p = _restaurant_profile()
        prompt = _build_extraction_prompt(
            "oi", "Olá!", p
        )
        assert "customer_name" in prompt
        assert "party_size" in prompt
        assert "reservation_date" in prompt
        assert "reservation_time" in prompt

    def test_prompt_contains_handoff_rules(self):
        p = _restaurant_profile()
        prompt = _build_extraction_prompt(
            "oi", "Olá!", p
        )
        assert "Cliente pede humano" in prompt

    def test_prompt_includes_existing_lead(self):
        p = _restaurant_profile()
        prompt = _build_extraction_prompt(
            "oi", "Olá!", p, existing_lead_summary="nome=João, data=sábado"
        )
        assert "nome=João" in prompt


class TestOfflineMode:
    @pytest.mark.asyncio
    @patch("app.services.lead_extractor.get_settings")
    async def test_offline_uses_heuristic(self, mock_settings):
        mock_settings.return_value.llm_provider = "fake"
        mock_settings.return_value.openai_api_key = None

        result = await extract_lead_data(
            "Meu nome é João, somos 4 pessoas",
            "Prazer, João!",
            _restaurant_profile(),
        )
        assert isinstance(result.detected_intent, (str, type(None)))
        keys = {f.key for f in result.extracted_fields}
        assert "customer_name" in keys


class TestLLMExtraction:
    @pytest.mark.asyncio
    @patch("app.services.lead_extractor.get_settings")
    @patch("openai.AsyncOpenAI")
    async def test_llm_extract_success(self, mock_openai_cls, mock_settings):
        mock_settings.return_value.llm_provider = "openai"
        mock_settings.return_value.openai_api_key = "sk-test"
        mock_settings.return_value.factory_model = "gpt-4.1-mini"

        # Mock the OpenAI client
        mock_client = AsyncMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = json.dumps({
            "detected_intent": "reserva",
            "intent_confidence": 0.9,
            "extracted_fields": [
                {"key": "customer_name", "value": "João", "confidence": 0.95},
                {"key": "party_size", "value": 8, "confidence": 0.9},
            ],
            "should_handoff": False,
        })
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await extract_lead_data(
            "Meu nome é João, somos 8 pessoas",
            "Prazer, João!",
            _restaurant_profile(),
        )
        assert result.detected_intent == "reserva"
        assert len(result.extracted_fields) == 2
        name = next(f for f in result.extracted_fields if f.key == "customer_name")
        assert name.value == "João"

    @pytest.mark.asyncio
    @patch("app.services.lead_extractor.get_settings")
    @patch("openai.AsyncOpenAI")
    async def test_llm_filters_disallowed_keys(self, mock_openai_cls, mock_settings):
        """LLM may return keys not in ConversationProfile.qualification_fields — must filter."""
        mock_settings.return_value.llm_provider = "openai"
        mock_settings.return_value.openai_api_key = "sk-test"
        mock_settings.return_value.factory_model = "gpt-4.1-mini"

        mock_client = AsyncMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = json.dumps({
            "extracted_fields": [
                {"key": "customer_name", "value": "João", "confidence": 0.95},
                {"key": "budget_range", "value": "ate_3k", "confidence": 0.7},  # NOT in allowed
                {"key": "credit_card", "value": "visa", "confidence": 0.7},  # NOT in allowed
            ],
            "should_handoff": False,
        })
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await extract_lead_data("Oi", "Oi!", _restaurant_profile())
        keys = {f.key for f in result.extracted_fields}
        assert "customer_name" in keys
        assert "budget_range" not in keys
        assert "credit_card" not in keys

    @pytest.mark.asyncio
    @patch("app.services.lead_extractor.get_settings")
    @patch("openai.AsyncOpenAI")
    async def test_llm_failure_falls_back_to_heuristic(self, mock_openai_cls, mock_settings):
        """If the LLM call raises, gracefully fall back to heuristic."""
        mock_settings.return_value.llm_provider = "openai"
        mock_settings.return_value.openai_api_key = "sk-test"
        mock_settings.return_value.factory_model = "gpt-4.1-mini"

        mock_client = AsyncMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))

        result = await extract_lead_data(
            "Meu nome é João, somos 4",
            "Prazer!",
            _restaurant_profile(),
        )
        # Heuristic should still extract at least the name
        name_field = next((f for f in result.extracted_fields if f.key == "customer_name"), None)
        assert name_field is not None
        assert name_field.value == "João"
