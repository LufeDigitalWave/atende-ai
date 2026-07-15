"""Dynamic prompt generation per niche.

Generates a tailored SDR agent system prompt based on the visitor's industry/niche.
Caches results in-memory to avoid regenerating for repeated niches.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from app.core.config import get_settings

logger = structlog.get_logger("prompt_factory")

META_PROMPT_PATH = Path(__file__).parent.parent / "agent" / "prompts" / "meta_prompt.md"


@dataclass
class NichePrompt:
    """Generated prompt for a niche."""
    agent_name: str
    company_name: str
    system_prompt: str
    suggestions: list[str] = field(default_factory=list)
    niche: str = ""


# In-memory cache (survives across requests, cleared on restart)
_cache: dict[str, NichePrompt] = {}


def _normalize_niche(niche: str) -> str:
    """Normalize niche string for cache key."""
    return niche.strip().lower()


async def generate_niche_prompt(niche: str) -> NichePrompt:
    """
    Generate a dynamic SDR prompt for the given niche.

    Uses OpenAI (gpt-4o-mini) to generate a tailored system prompt.
    Caches result in-memory.
    """
    key = _normalize_niche(niche)

    # Check cache
    if key in _cache:
        logger.info(f"prompt cache hit for niche: {key}")
        return _cache[key]

    settings = get_settings()

    # Load meta-prompt template
    meta_prompt_template = META_PROMPT_PATH.read_text(encoding="utf-8")
    meta_prompt = meta_prompt_template.replace("{niche}", niche)

    # Generate via LLM
    if settings.llm_provider == "fake":
        # Offline fallback: return a generic prompt
        result = _fake_generate(niche)
    else:
        result = await _llm_generate(niche, meta_prompt)

    result.niche = niche
    _cache[key] = result
    logger.info(f"generated prompt for niche: {key}, agent: {result.agent_name}")
    return result


async def _llm_generate(niche: str, meta_prompt: str) -> NichePrompt:
    """Call OpenAI to generate the niche prompt."""
    import openai
    from app.core.config import get_settings

    settings = get_settings()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": meta_prompt},
                {"role": "user", "content": f"Gere o agente SDR para o nicho: {niche}"},
            ],
            temperature=0.8,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        return NichePrompt(
            agent_name=data.get("agent_name", "Sofia"),
            company_name=data.get("company_name", "Empresa Demo"),
            system_prompt=data.get("system_prompt", ""),
            suggestions=data.get("suggestions", [
                "Quero saber mais sobre seus serviços",
                "Quanto custa?",
                "Vocês atendem hoje?",
            ]),
        )

    except Exception as e:
        logger.error(f"LLM generation failed: {e}, falling back to generic")
        return _fake_generate(niche)


def _fake_generate(niche: str) -> NichePrompt:
    """Offline fallback: generic prompt."""
    return NichePrompt(
        agent_name="Sofia",
        company_name=f"Empresa {niche.title()}",
        system_prompt=f"""Você é Sofia, SDR de IA da Empresa {niche.title()}.

Sua missão é qualificar leads coletando: nome, serviço de interesse, queixa/objetivo, faixa de orçamento e urgência.

Regras:
- Uma pergunta por vez
- Tom caloroso-profissional, PT-BR natural
- Mensagens curtas (máx 280 chars)
- Máx 1 emoji por mensagem
- Nunca invente preço — diga "vou confirmar com a equipe"
- Quando 5 campos completos, proponha agendamento

Serviços disponíveis (fictícios):
- Serviço básico: a partir de 12x R$ 99 ou R$ 1.188 à vista
- Serviço premium: a partir de 12x R$ 249 ou R$ 2.988 à vista
- Pacote completo: a partir de 12x R$ 399 ou R$ 4.788 à vista

Ramo: {niche}""",
        suggestions=[
            f"Quero saber sobre {niche}",
            "Quanto custa o serviço de vocês?",
            "Vocês atendem hoje?",
        ],
    )


def get_cached_prompt(niche: str) -> NichePrompt | None:
    """Get cached prompt without generating."""
    key = _normalize_niche(niche)
    return _cache.get(key)


def clear_cache() -> None:
    """Clear all cached prompts (used by reset job)."""
    _cache.clear()
