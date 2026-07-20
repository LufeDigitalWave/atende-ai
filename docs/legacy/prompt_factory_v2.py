"""Prompt Factory v2 — generates DATA (BusinessProfile), not instructions.

Architecture:
  niche → [meta-prompt → LLM → BusinessProfile JSON] → Pydantic validation
        → render agent_template_v2.md with the profile
        → final system prompt (cached in-memory, TTL 1h)

The LLM (gpt-4.1-mini) only produces structured data.
The battle-tested rules live in the TEMPLATE (versionado, com changelog).
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog
from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.business_profile import BusinessProfile

logger = structlog.get_logger("prompt_factory")

META_PROMPT_PATH = Path(__file__).parent.parent / "agent" / "prompts" / "factory_v2.md"
TEMPLATE_PATH = Path(__file__).parent.parent / "agent" / "prompts" / "agent_template_v2.md"

# Fallback static profile (clinica estetica) — used when LLM fails
FALLBACK_PROFILE = BusinessProfile(
    agent_name="Sofia",
    company_name="Clínica Renova",
    city="São Paulo",
    tagline="Estética avançada com protocolo personalizado",
    services=[
        {
            "name": "Limpeza de pele profunda",
            "price_installments": "12x R$ 89",
            "price_cash": "R$ 1.068",
            "duration_or_scope": "60 min",
            "highlight": False,
        },
        {
            "name": "Peeling químico médio",
            "price_installments": "12x R$ 180",
            "price_cash": "R$ 2.160",
            "duration_or_scope": "4 sessões quinzenais",
            "highlight": True,
        },
        {
            "name": "Microagulhamento com drug delivery",
            "price_installments": "12x R$ 250",
            "price_cash": "R$ 3.000",
            "duration_or_scope": "3 sessões mensais",
            "highlight": True,
        },
    ],
    qualification_extra_question="Qual região do corpo ou rosto te incomoda mais?",
    faq=[
        {"q": "Qual o horário de atendimento?", "a": "De segunda a sexta das 9h às 20h, sábados das 9h às 14h."},
        {"q": "Onde fica a clínica?", "a": "Rua das Flores, 123 — Jardins, São Paulo/SP."},
        {"q": "Quais formas de pagamento?", "a": "Pix, cartão (até 12x) e boleto."},
        {"q": "Qual o diferencial de vocês?", "a": "Protocolos personalizados com avaliação gratuita e acompanhamento pós."},
        {"q": "Precisa de preparo antes do procedimento?", "a": "Depende do protocolo — na avaliação a gente orienta tudo certinho."},
    ],
    common_objections=[
        {"objection": "Está caro", "guideline": "Valorize o protocolo personalizado e a avaliação gratuita. Nunca dê desconto."},
        {"objection": "Tenho medo de dor", "guideline": "Explique que usamos anestésico tópico e que o desconforto é mínimo."},
        {"objection": "Vou pensar", "guideline": "Respeite, reforce a avaliação gratuita e pergunte se pode entrar em contato em 2 dias."},
    ],
    tone_notes="calorosa, profissional, empática",
    opening_message="Oi! Sou a Sofia da Clínica Renova 😊 Como posso ajudar você hoje?",
    suggestions=[
        "Quero saber sobre tratamento pra melasma",
        "Quanto custa uma limpeza de pele?",
        "Vocês atendem sábado?",
    ],
)

# Cache TTL in seconds (1 hour)
CACHE_TTL = 3600


@dataclass
class CachedProfile:
    """Cached profile with timestamp."""
    profile: BusinessProfile
    system_prompt: str
    created_at: float = field(default_factory=time.time)

    @property
    def expired(self) -> bool:
        return (time.time() - self.created_at) > CACHE_TTL


# In-memory cache
_cache: dict[str, CachedProfile] = {}


def sanitize_niche(niche: str) -> str:
    """Sanitize niche input to prevent injection.

    - Max 60 chars
    - No line breaks
    - Strip control characters
    - If empty/invalid, default to 'consultoria empresarial'
    """
    # Remove line breaks and control chars
    cleaned = re.sub(r"[\n\r\t\x00-\x1f]", " ", niche)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Max length
    cleaned = cleaned[:60]
    # If empty or too short, fallback
    if len(cleaned) < 3:
        cleaned = "consultoria empresarial"
    return cleaned


def _normalize_cache_key(niche: str) -> str:
    """Normalize for cache lookup."""
    return niche.strip().lower()


def render_template(profile: BusinessProfile) -> str:
    """Render agent_template_v2.md with profile data."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Render services
    services_lines = []
    for s in profile.services:
        highlight = " ⭐" if s.highlight else ""
        services_lines.append(
            f"- **{s.name}**{highlight}: {s.price_installments} ou {s.price_cash} à vista "
            f"({s.duration_or_scope})"
        )
    services_rendered = "\n".join(services_lines)

    # Render FAQ
    faq_lines = [f"- **{f.q}** — {f.a}" for f in profile.faq]
    faq_rendered = "\n".join(faq_lines)

    # Render objections
    obj_lines = [f"- \"{o.objection}\" → {o.guideline}" for o in profile.common_objections]
    objections_rendered = "\n".join(obj_lines)

    # Replace placeholders
    result = template.replace("{agent_name}", profile.agent_name)
    result = result.replace("{company_name}", profile.company_name)
    result = result.replace("{city}", profile.city)
    result = result.replace("{tagline}", profile.tagline)
    result = result.replace("{qualification_extra_question}", profile.qualification_extra_question)
    result = result.replace("{tone_notes}", profile.tone_notes)
    result = result.replace("{services_rendered}", services_rendered)
    result = result.replace("{faq_rendered}", faq_rendered)
    result = result.replace("{objections_rendered}", objections_rendered)

    return result


async def generate_niche_prompt(niche: str) -> CachedProfile:
    """
    Generate a dynamic SDR prompt for the given niche.

    Uses gpt-4.1-mini to generate a BusinessProfile JSON.
    Validates with Pydantic, renders template, caches result.
    """
    safe_niche = sanitize_niche(niche)
    key = _normalize_cache_key(safe_niche)

    # Check cache (with TTL)
    if key in _cache and not _cache[key].expired:
        logger.info(f"prompt cache hit for niche: {key}")
        return _cache[key]

    settings = get_settings()

    # Generate profile
    if settings.llm_provider == "fake" and not settings.openai_api_key:
        # Full offline mode: use fallback
        profile = FALLBACK_PROFILE
    else:
        profile = await _generate_profile(safe_niche)

    # Render template
    system_prompt = render_template(profile)

    # Cache
    cached = CachedProfile(profile=profile, system_prompt=system_prompt)
    _cache[key] = cached
    logger.info(f"generated profile for niche: {key}, agent: {profile.agent_name}")
    return cached


async def _generate_profile(niche: str) -> BusinessProfile:
    """Call gpt-4.1-mini to generate a BusinessProfile.

    Retry once on validation failure, then fallback to static profile.
    """
    import openai

    settings = get_settings()

    if not settings.openai_api_key:
        logger.warning("no OpenAI key for factory, using fallback")
        return FALLBACK_PROFILE

    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    meta_prompt = META_PROMPT_PATH.read_text(encoding="utf-8")
    meta_prompt = meta_prompt.replace("{NICHE}", niche)

    factory_model = getattr(settings, "factory_model", "gpt-4.1-mini")

    for attempt in range(2):  # max 1 retry
        try:
            response = await client.chat.completions.create(
                model=factory_model,
                messages=[
                    {"role": "system", "content": meta_prompt},
                    {"role": "user", "content": f"Gere o perfil para o nicho: {niche}"},
                ],
                temperature=0.7,
                max_tokens=2048,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content
            data = json.loads(raw)
            profile = BusinessProfile(**data)
            return profile

        except (ValidationError, json.JSONDecodeError, KeyError) as e:
            logger.warning(
                f"factory validation failed (attempt {attempt + 1}): {e}"
            )
            if attempt == 0:
                continue  # retry once
            logger.error("factory failed after retry, using fallback")
            return FALLBACK_PROFILE

        except Exception as e:
            logger.error(f"factory LLM call failed: {e}")
            return FALLBACK_PROFILE

    return FALLBACK_PROFILE


def get_cached_prompt(niche: str) -> CachedProfile | None:
    """Get cached profile without generating. Returns None if not cached or expired."""
    key = _normalize_cache_key(sanitize_niche(niche))
    cached = _cache.get(key)
    if cached and not cached.expired:
        return cached
    return None


def clear_cache() -> None:
    """Clear all cached profiles (used by reset job)."""
    _cache.clear()
