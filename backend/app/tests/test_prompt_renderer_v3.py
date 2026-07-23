"""Tests for Prompt Renderer v3 (Layer 2 of v3 architecture)."""

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
from app.services.prompt_factory_v3 import FALLBACK_PROFILE
from app.services.prompt_renderer_v3 import (
    _render_faq,
    _render_handoff_rules,
    _render_journeys,
    _render_objections,
    _render_prohibited_behaviors,
    _render_qualification_fields,
    _render_services,
    render_prompt,
)


def _restaurant_profile() -> NicheProfile:
    """Build a synthetic restaurant NicheProfile for renderer tests."""
    business = BusinessProfile(
        agent_name="Mariana",
        company_name="Sabor da Terra",
        city="Curitiba",
        tagline="Culinária brasileira regional",
        services=[
            ServiceItem(
                name="Almoço Executivo",
                price_installments="1x R$ 49",
                price_cash="R$ 49",
                duration_or_scope="1h30",
                highlight=True,
            ),
            ServiceItem(
                name="Rodízio",
                price_installments="1x R$ 89",
                price_cash="R$ 89",
                duration_or_scope="2h",
                highlight=False,
            ),
            ServiceItem(
                name="Jantar à la carte",
                price_installments="1x R$ 79",
                price_cash="R$ 79",
                duration_or_scope="2h",
                highlight=False,
            ),
        ],
        qualification_extra_question="Qual tipo de cozinha você prefere?",
        faq=[
            FAQItem(q="Vocês têm delivery?", a="Sim, iFood e Rappi."),
            FAQItem(q="Atendem quantas pessoas?", a="Mesas pra até 6 pessoas."),
            FAQItem(q="Tem vegetariano?", a="Sim, prato vegetariano."),
            FAQItem(q="Aceitam cartão?", a="Todos, crédito e débito."),
            FAQItem(q="Tem estacionamento?", a="Conveniado ao lado."),
        ],
        common_objections=[
            ObjectionItem(objection="Tá caro", guideline="Valorize o buffet."),
            ObjectionItem(objection="Demora?", guideline="Diga que reservas reduzem espera."),
            ObjectionItem(objection="Vou pensar", guideline="Reforce horário de pico."),
        ],
        tone_notes="acolhedora, prestativa",
        opening_message="Olá! Sou a Mariana, do Sabor da Terra.",
        suggestions=["Quais pratos vocês têm?", "Vocês têm almoço?", "Posso fazer reserva?"],
    )
    conversation = ConversationProfile(
        business_mode="reservation_based",
        primary_intents=["cardapio", "reserva", "delivery", "horarios", "localizacao"],
        journeys=[
            ConversationJourney(
                intent="reserva",
                description="Cliente quer reservar mesa",
                response_goal="Confirmar reserva com data, horário e quantidade de pessoas",
                suggested_cta="Posso te ajudar com a reserva.",
                qualification_fields=["customer_name", "party_size", "reservation_date", "reservation_time"],
                handoff_conditions=["date + party_size + time confirmados"],
                forbidden_questions=["Não perguntar faixa de investimento"],
            ),
        ],
        qualification_fields=[
            QualificationField(key="customer_name", label="Nome", purpose="Personalizar reserva", priority="medium"),
            QualificationField(key="party_size", label="Quantidade de pessoas", purpose="Organizar mesa", required_for=["reserva"], priority="high"),
            QualificationField(key="reservation_date", label="Data", purpose="Verificar disponibilidade", required_for=["reserva"], priority="high"),
            QualificationField(key="reservation_time", label="Horário", purpose="Reservar slot", required_for=["reserva"], priority="high"),
        ],
        recommended_ctas=["Posso te ajudar com a reserva.", "Quer que eu verifique disponibilidade?"],
        prohibited_behaviors=[
            "Não perguntar faixa de investimento para almoço",
            "Não tratar reserva simples como venda consultiva",
        ],
        handoff_rules=[
            "Cliente pede humano",
            "Reserva completa (data + horário + pessoas + nome)",
        ],
        proactive_opening_strategy="Apresentar opções de almoço/jantar e oferecer reserva",
        response_before_qualification=True,
        max_questions_per_message=1,
    )
    return NicheProfile(business=business, conversation=conversation)


class TestSectionRenderers:
    def test_render_services(self):
        p = _restaurant_profile()
        out = _render_services(p.business)
        assert "Almoço Executivo" in out
        assert "1x R$ 49" in out
        assert "⭐" in out  # highlight
        assert "Rodízio" in out
        empty_business = _restaurant_profile().business.model_copy(deep=True)
        empty_business.services = [
            ServiceItem(name="Svc", price_installments="1x R$ 10", price_cash="R$ 10", duration_or_scope="30min", highlight=False)
        ] * 3
        out = _render_services(empty_business)
        assert "⭐" not in out

    def test_render_faq(self):
        p = _restaurant_profile()
        out = _render_faq(p.business)
        assert "delivery?" in out
        assert "iFood e Rappi" in out

    def test_render_journeys(self):
        p = _restaurant_profile()
        out = _render_journeys(p.conversation)
        assert "### reserva" in out
        assert "party_size" in out
        assert "NÃO pergunte" in out
        assert "Não perguntar faixa de investimento" in out

    def test_render_qualification_fields(self):
        p = _restaurant_profile()
        out = _render_qualification_fields(p.conversation)
        assert "Quantidade de pessoas" in out
        assert "[prioridade: high]" in out
        assert "[só quando relevante]" in out
        assert "obrigatório pra: reserva" in out

    def test_render_prohibited_behaviors(self):
        p = _restaurant_profile()
        out = _render_prohibited_behaviors(p.conversation)
        assert "Não perguntar faixa de investimento" in out
        assert "Não tratar reserva simples" in out

    def test_render_objections(self):
        p = _restaurant_profile()
        out = _render_objections(p.business)
        assert "Tá caro" in out
        assert "Valorize o buffet" in out

    def test_render_handoff_rules(self):
        p = _restaurant_profile()
        out = _render_handoff_rules(p.conversation)
        assert "Cliente pede humano" in out
        assert "Reserva completa" in out


class TestRenderPrompt:
    def test_renders_without_error(self):
        p = _restaurant_profile()
        prompt = render_prompt(p)
        assert len(prompt) > 1000

    def test_contains_company_identity(self):
        p = _restaurant_profile()
        prompt = render_prompt(p)
        assert "Mariana" in prompt
        assert "Sabor da Terra" in prompt
        assert "Curitiba" in prompt

    def test_contains_journey_section(self):
        p = _restaurant_profile()
        prompt = render_prompt(p)
        assert "### reserva" in prompt
        assert "Confirmar reserva" in prompt

    def test_contains_prohibited_behaviors(self):
        p = _restaurant_profile()
        prompt = render_prompt(p)
        assert "Não perguntar faixa de investimento" in prompt

    def test_contains_opening_strategy(self):
        p = _restaurant_profile()
        prompt = render_prompt(p)
        assert "Apresentar opções de almoço/jantar" in prompt

    def test_no_unfilled_placeholders(self):
        p = _restaurant_profile()
        prompt = render_prompt(p)
        import re
        leftover = re.findall(r"\{[a-z_]+\}", prompt)
        assert leftover == [], f"unfilled placeholders: {leftover}"

    def test_fallback_profile_renders(self):
        prompt = render_prompt(FALLBACK_PROFILE)
        assert "Sofia" in prompt
        assert "Clínica Renova" in prompt
        assert "appointment_based" not in prompt  # business_mode is metadata, not exposed

    def test_no_5_universal_fields_language(self):
        """The v3 template must NOT require 5 universal fields."""
        p = _restaurant_profile()
        prompt = render_prompt(p)
        # v2 template had "5. Urgência" as mandatory; v3 must not.
        # The MISSÃO section now says "responder ANTES de pedir informações"
        assert "ANTES de pedir" in prompt
        # Qualification section says "quando relevante"
        assert "só quando relevante" in prompt
        # Prohibited behaviors mention NOT asking for budget in transactional
        assert "Não perguntar faixa de investimento" in prompt
        # The MISSÃO must NOT have a numbered list ending at "5. Urgência"
        # v3's MISSÃO has 6 items (about behavior, not fields)
        assert "Coletar apenas dados úteis para a intenção atual" in prompt
