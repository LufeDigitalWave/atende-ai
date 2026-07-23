"""Prompt Factory v3 — generates BusinessProfile + ConversationProfile per niche.

Architecture (Layer 1 of 3):
  niche → sanitize → gpt-4.1-mini (factory_v3.md)
        → JSON { business: {...}, conversation: {...} }
        → Pydantic validate (BusinessProfile + ConversationProfile)
        → NicheProfile (validated package)
        → cache (TTL 1h)

Generates DATA only. Never instructions.
Templates render this into a system prompt — the agent template is a separate file.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from app.core.config import get_settings
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

logger = structlog.get_logger("prompt_factory_v3")

META_PROMPT_PATH = Path(__file__).parent.parent / "agent" / "prompts" / "factory_v3.md"

CACHE_TTL = 3600  # 1 hour


# ============================================================
# FALLBACK profile (Sofia / Clínica Renova) — used when LLM fails
# ============================================================

def _fallback_business() -> BusinessProfile:
    return BusinessProfile(
        agent_name="Sofia",
        company_name="Clínica Renova",
        city="São Paulo",
        tagline="Estética avançada com protocolo personalizado",
        services=[
            ServiceItem(
                name="Limpeza de pele profunda",
                price_installments="12x R$ 89",
                price_cash="R$ 1.068",
                duration_or_scope="60 min",
                highlight=False,
            ),
            ServiceItem(
                name="Peeling químico médio",
                price_installments="12x R$ 180",
                price_cash="R$ 2.160",
                duration_or_scope="4 sessões quinzenais",
                highlight=True,
            ),
            ServiceItem(
                name="Microagulhamento com drug delivery",
                price_installments="12x R$ 250",
                price_cash="R$ 3.000",
                duration_or_scope="3 sessões mensais",
                highlight=True,
            ),
        ],
        qualification_extra_question="Qual região do corpo ou rosto te incomoda mais?",
        faq=[
            FAQItem(q="Qual o horário de atendimento?", a="De segunda a sexta das 9h às 20h, sábados das 9h às 14h."),
            FAQItem(q="Onde fica a clínica?", a="Rua das Flores, 123 — Jardins, São Paulo/SP."),
            FAQItem(q="Quais formas de pagamento?", a="Pix, cartão (até 12x) e boleto."),
            FAQItem(q="Qual o diferencial de vocês?", a="Protocolos personalizados com avaliação gratuita e acompanhamento pós."),
            FAQItem(q="Precisa de preparo antes do procedimento?", a="Depende do protocolo — na avaliação a gente orienta tudo certinho."),
        ],
        common_objections=[
            ObjectionItem(objection="Está caro", guideline="Valorize o protocolo personalizado e a avaliação gratuita. Nunca dê desconto."),
            ObjectionItem(objection="Tenho medo de dor", guideline="Explique que usamos anestésico tópico e que o desconforto é mínimo."),
            ObjectionItem(objection="Vou pensar", guideline="Respeite, reforce a avaliação gratuita e pergunte se pode entrar em contato em 2 dias."),
        ],
        tone_notes="calorosa, profissional, empática",
        opening_message="Oi! Sou a Sofia da Clínica Renova 😊 Como posso ajudar você hoje?",
        suggestions=[
            "Quero saber sobre tratamento pra melasma",
            "Quanto custa uma limpeza de pele?",
            "Vocês atendem sábado?",
        ],
    )


def _fallback_conversation() -> ConversationProfile:
    return ConversationProfile(
        business_mode="appointment_based",
        primary_intents=["avaliacao", "procedimento", "horario", "preco", "duvida"],
        journeys=[
            ConversationJourney(
                intent="avaliacao",
                description="Cliente quer agendar uma avaliação inicial",
                response_goal="Confirmar agendamento de avaliação gratuita",
                suggested_cta="Posso verificar um horário para avaliação gratuita.",
                qualification_fields=["customer_name", "need", "urgency", "availability"],
                handoff_conditions=["Necessidade + urgência + disponibilidade informadas"],
                forbidden_questions=["Não prometer resultado clínico", "Não inventar preço fora da base"],
            ),
        ],
        qualification_fields=[
            QualificationField(key="customer_name", label="Nome", purpose="Personalizar atendimento", priority="medium"),
            QualificationField(key="need", label="Necessidade", purpose="Identificar tratamento", required_for=["avaliacao"], priority="high"),
            QualificationField(key="urgency", label="Urgência", purpose="Priorizar agendamento", priority="medium"),
            QualificationField(key="availability", label="Disponibilidade", purpose="Sugerir horários", priority="medium"),
        ],
        recommended_ctas=["Posso verificar um horário para você.", "Quer que eu agende uma avaliação?"],
        prohibited_behaviors=[
            "Não prometer resultado clínico",
            "Não dar desconto agressivo",
            "Não inventar preço fora da base",
        ],
        handoff_rules=["Cliente pede humano", "Lead qualificado (necessidade + urgência + disponibilidade)"],
        lead_scoring_rules={"need_filled": 20, "urgency_high": 15, "availability_filled": 15},
        proactive_opening_strategy="Apresentar-se brevemente e oferecer caminhos: avaliação, dúvidas sobre serviços, horários.",
        response_before_qualification=True,
        max_questions_per_message=1,
    )


FALLBACK_PROFILE = NicheProfile(
    business=_fallback_business(),
    conversation=_fallback_conversation(),
)


# ============================================================
# Cache
# ============================================================

@dataclass
class CachedProfile:
    profile: NicheProfile
    created_at: float = field(default_factory=time.time)

    @property
    def expired(self) -> bool:
        return (time.time() - self.created_at) > CACHE_TTL


_cache: dict[str, CachedProfile] = {}


# ============================================================
# Sanitization (injection prevention)
# ============================================================

def sanitize_niche(niche: str) -> str:
    """Sanitize niche input to prevent prompt injection."""
    cleaned = re.sub(r"[\n\r\t\x00-\x1f]", " ", niche)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned[:60]
    if len(cleaned) < 3:
        cleaned = "consultoria empresarial"
    return cleaned


def _cache_key(niche: str) -> str:
    return niche.strip().lower()


# ============================================================
# Main factory function
# ============================================================

async def generate_niche_profile(niche: str) -> NicheProfile:
    """Generate a complete NicheProfile (Business + Conversation) for the niche.

    Returns the FALLBACK_PROFILE on LLM failure or invalid JSON.
    Caches successful results for 1 hour.
    """
    safe = sanitize_niche(niche)
    key = _cache_key(safe)

    # Cache hit?
    if key in _cache and not _cache[key].expired:
        logger.info(f"v3 cache hit for niche: {key}")
        return _cache[key].profile

    settings = get_settings()

    # Offline / no API key?
    if settings.llm_provider == "fake" and not settings.openai_api_key:
        logger.info(f"v3 offline mode — using fallback for: {safe}")
        _cache[key] = CachedProfile(profile=FALLBACK_PROFILE)
        return FALLBACK_PROFILE

    # Try LLM with 1 retry
    profile = None
    for attempt in range(2):
        try:
            profile = await _llm_generate_profile(safe)
            break
        except Exception as e:
            logger.warning(f"v3 factory attempt {attempt + 1} failed: {e}")
            if attempt == 0:
                continue
            profile = FALLBACK_PROFILE

    # Cache and return
    _cache[key] = CachedProfile(profile=profile)
    logger.info(f"v3 generated profile for: {safe} (agent={profile.business.agent_name})")
    return profile


async def _llm_generate_profile(niche: str) -> NicheProfile:
    """Call gpt-4.1-mini to generate BusinessProfile + ConversationProfile."""
    import openai

    settings = get_settings()
    if not settings.openai_api_key:
        return FALLBACK_PROFILE

    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    factory_model = getattr(settings, "factory_model", "gpt-4.1-mini")

    meta_prompt = META_PROMPT_PATH.read_text(encoding="utf-8")
    meta_prompt = meta_prompt.replace("{NICHE}", niche)

    response = await client.chat.completions.create(
        model=factory_model,
        messages=[
            {"role": "system", "content": meta_prompt},
            {"role": "user", "content": f"Gere os perfis para o nicho: {niche}"},
        ],
        temperature=0.7,
        max_tokens=3000,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    # Validate each part separately (Pydantic per schema, fail-soft)
    business = BusinessProfile(**data.get("business", data))  # fallback to top-level for compat
    conversation = ConversationProfile(**data.get("conversation", {
        "business_mode": "mixed",
        "primary_intents": data.get("primary_intents", ["saudacao", "duvida", "agendamento"]),
        "journeys": [{
            "intent": "duvida",
            "description": "Cliente tem uma dúvida geral",
            "response_goal": "Responder a dúvida",
            "suggested_cta": "Posso te ajudar?",
            "qualification_fields": ["customer_name"],
            "handoff_conditions": ["Cliente pede humano"],
            "forbidden_questions": ["Não inventar preço"],
        }],
        "qualification_fields": [{"key": "customer_name", "label": "Nome", "purpose": "Personalizar"}],
        "prohibited_behaviors": ["Não inventar informações"],
        "handoff_rules": ["Cliente pede humano"],
        "proactive_opening_strategy": "Apresentar-se e oferecer caminhos.",
    }))

    return NicheProfile(business=business, conversation=conversation)


# ============================================================
# Cache access
# ============================================================

def get_cached_profile(niche: str) -> NicheProfile | None:
    key = _cache_key(sanitize_niche(niche))
    cached = _cache.get(key)
    if cached and not cached.expired:
        return cached.profile
    return None


def clear_cache() -> None:
    _cache.clear()
