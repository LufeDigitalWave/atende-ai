"""LLM-based lead extractor — replaces the heuristic hardcoded extractor.

This is Layer 4 of the v3 architecture. It:
- Receives the user's message, the agent's response, and the ConversationProfile
- Calls gpt-4.1-mini (or claude-haiku) via tool use / JSON mode
- Returns ExtractedLeadData with detected_intent, intent_confidence,
  extracted_fields (per key with confidence), should_handoff, handoff_reason
- Validates against ConversationProfile.qualification_fields (allowed keys only)
- Falls back to legacy heuristic if LLM fails (graceful degradation)
"""
from __future__ import annotations

import json
import structlog
from typing import Any

import openai
from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.conversation_profile import ConversationProfile
from app.schemas.lead_extraction import (
    ExtractedField,
    ExtractedLeadData,
)
from app.schemas.niche_profile import NicheProfile

logger = structlog.get_logger("lead_extractor")


# ============================================================
# Tool schema for OpenAI tool use
# ============================================================

EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_lead_data",
        "description": "Extract structured lead data from the visitor's message and the agent's response.",
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Brief chain-of-thought (max 200 chars): what intent does the visitor have? Which fields are explicitly stated vs implied? This helps calibrate confidence.",
                },
                "detected_intent": {
                    "type": "string",
                    "description": "Which intent from the conversation profile matches (e.g., 'reserva', 'avaliacao', 'cardapio')",
                },
                "intent_confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "How confident about the detected intent (0-1)",
                },
                "extracted_fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "Field key from the profile"},
                            "value": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "number"},
                                    {"type": "boolean"},
                                    {"type": "null"},
                                ],
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["key", "value", "confidence"],
                    },
                },
                "should_handoff": {
                    "type": "boolean",
                    "description": "Whether to trigger handoff to a human",
                },
                "handoff_reason": {
                    "type": "string",
                    "description": "If handoff: why (e.g., 'Cliente pediu humano explicitamente')",
                },
                "lead_stage_suggestion": {
                    "type": "string",
                    "description": "Suggested lead state (novo, em_qualificacao, qualificado, handoff)",
                },
                "notes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Internal observations (not shown to visitor)",
                },
            },
            "required": ["extracted_fields", "should_handoff"],
        },
    },
}


# ============================================================
# Prompt builder
# ============================================================

def _build_extraction_prompt(
    user_message: str,
    agent_response: str,
    profile: NicheProfile,
    existing_lead_summary: str | None = None,
) -> str:
    """Build the system prompt for the extractor LLM."""
    allowed_keys = [qf.key for qf in profile.conversation.qualification_fields]
    primary_intents = profile.conversation.primary_intents
    handoff_rules = profile.conversation.handoff_rules
    prohibited = profile.conversation.prohibited_behaviors

    prompt = f"""Você é um extrator de dados de leads. Recebe a mensagem do visitante
e a resposta do agente, e extrai APENAS dados estruturados que atualizem o CRM.

# Contexto do nicho
Empresa: {profile.business.company_name}
Modo de operação: {profile.conversation.business_mode}
Agente: {profile.business.agent_name}

# Intenções possíveis (escolha a que melhor match)
{', '.join(primary_intents)}

# Campos que você PODE extrair (use SOMENTE estes)
{', '.join(allowed_keys)}

# Regras para handoff
Acione handoff quando QUALQUER destas condições for verdadeira:
{chr(10).join(f'- {r}' for r in handoff_rules)}

# Comportamentos PROIBIDOS do agente (se detectar no diálogo, sinalize)
{chr(10).join(f'- {p}' for p in prohibited)}

# Estado atual do lead (campos já preenchidos — NÃO sobrescreva a menos que tenha evidência nova)
{existing_lead_summary or '(lead vazio)'}

# Instruções estritas
- PRIMEIRO preencha o campo "reasoning" com um raciocínio breve (max 200 chars):
  pense: qual é a intenção do visitante? Quais campos estão explícitos vs implícitos?
- Extraia APENAS dados presentes na mensagem do visitante ou resposta do agente
- Se um campo não foi mencionado, NÃO invente valor (retorne value=null)
- confidence: use 0.9+ se explícito, 0.6-0.8 se implícito, <0.5 se incerto
- Se o visitante pedir humano explicitamente (palavras como 'atendente', 'humano', 'pessoa real'), SEMPRE should_handoff=true
- NUNCA invente dados fora do que o visitante disse
- detected_intent: null se a mensagem não tem intenção clara (ex: 'oi', 'obrigado')
"""
    return prompt


# ============================================================
# Main extractor
# ============================================================

async def extract_lead_data(
    user_message: str,
    agent_response: str,
    profile: NicheProfile,
    existing_lead_summary: str | None = None,
) -> ExtractedLeadData:
    """Extract structured lead data via LLM.

    Falls back to heuristic extraction if LLM is unavailable.
    """
    settings = get_settings()

    # No API key / fake mode → heuristic fallback
    if settings.llm_provider == "fake" and not settings.openai_api_key:
        logger.info("extractor: offline mode, using heuristic fallback")
        return _heuristic_fallback(user_message, agent_response, profile)

    # Real API call
    try:
        return await _llm_extract(user_message, agent_response, profile, existing_lead_summary)
    except Exception as e:
        logger.warning(f"extractor: LLM call failed ({e}), using heuristic fallback")
        return _heuristic_fallback(user_message, agent_response, profile)


async def _llm_extract(
    user_message: str,
    agent_response: str,
    profile: NicheProfile,
    existing_lead_summary: str | None,
) -> ExtractedLeadData:
    """Call gpt-4.1-mini to extract lead data via tool use."""
    settings = get_settings()

    factory_model = getattr(settings, "factory_model", "gpt-4.1-mini")

    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    system_prompt = _build_extraction_prompt(
        user_message, agent_response, profile, existing_lead_summary
    )

    response = await client.chat.completions.create(
        model=factory_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Mensagem do visitante: {user_message}\n\nResposta do agente: {agent_response}"},
        ],
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "function", "function": {"name": "extract_lead_data"}},
        temperature=0.1,
        max_tokens=500,
    )

    # Log extraction token usage (best-effort)
    try:
        from app.services.budget import log_usage
        from app.core.database import get_session_factory

        usage = response.usage
        if usage:
            async with get_session_factory()() as db_session:
                await log_usage(
                    db_session,
                    session_id=None,  # extraction is not tied to a specific session
                    call_type="extraction",
                    model=factory_model,
                    input_tokens=usage.prompt_tokens or 0,
                    output_tokens=usage.completion_tokens or 0,
                    cached_tokens=0,
                )
    except Exception as e:
        logger.warning(f"log_usage failed (extraction): {e}")

    message = response.choices[0].message
    if not message.tool_calls:
        # No tool call — treat as empty extraction
        return ExtractedLeadData()

    tool_call = message.tool_calls[0]
    try:
        data = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        logger.warning(f"extractor: invalid JSON in tool call: {e}")
        return _heuristic_fallback(user_message, agent_response, profile)

    # Convert to ExtractedLeadData, validating against allowed keys
    allowed_keys = {qf.key for qf in profile.conversation.qualification_fields}
    extracted_fields = []
    for ef in data.get("extracted_fields", []):
        if ef.get("key") not in allowed_keys:
            # Filter out disallowed keys silently
            logger.debug(f"extractor: ignoring disallowed key: {ef.get('key')}")
            continue
        try:
            extracted_fields.append(ExtractedField(
                key=ef["key"],
                value=ef.get("value"),
                confidence=ef.get("confidence", 0.5),
            ))
        except ValidationError:
            continue

    return ExtractedLeadData(
        detected_intent=data.get("detected_intent"),
        intent_confidence=data.get("intent_confidence", 0.0),
        extracted_fields=extracted_fields,
        should_handoff=bool(data.get("should_handoff", False)),
        handoff_reason=data.get("handoff_reason"),
        lead_stage_suggestion=data.get("lead_stage_suggestion"),
        notes=data.get("notes", []),
    )


# ============================================================
# Heuristic fallback (graceful degradation when LLM unavailable)
# ============================================================

def _heuristic_fallback(
    user_message: str,
    agent_response: str,
    profile: NicheProfile,
) -> ExtractedLeadData:
    """Conservative heuristic extraction. Only matches generic patterns."""
    import re

    text = f"{user_message} {agent_response}".lower()
    extracted_fields: list[ExtractedField] = []
    handoff = False
    handoff_reason: str | None = None
    detected_intent: str | None = None

    # Generic name extraction (any title-cased word)
    name_match = re.search(r"\bmeu nome [eé] (\w+)", text, re.IGNORECASE)
    if not name_match:
        # Find the name the agent repeated (e.g., "Obrigada, Luiz!")
        match = re.search(r"(?:obrigad[oa]|prazer|perfeito|ótimo|otimo),?\s+([A-ZÁÉÍÓÚÂÊÔÇ][a-záéíóúâêôç]+)", agent_response, re.IGNORECASE)
        if match:
            name_match = match
    if name_match:
        extracted_fields.append(ExtractedField(
            key="customer_name",
            value=name_match.group(1).capitalize(),
            confidence=0.85,
        ))

    # Generic party_size
    for pattern in [r"\b(\d+)\s*pessoas?\b", r"\bsomos\s+(\d+)\b", r"\bpara\s+(\d+)\b"]:
        m = re.search(pattern, text)
        if m:
            try:
                extracted_fields.append(ExtractedField(
                    key="party_size",
                    value=int(m.group(1)),
                    confidence=0.85,
                ))
            except ValueError:
                pass
            break

    # Generic date/time patterns
    for kw in ["hoje", "amanhã", "amanha", "agora", "agora mesmo"]:
        if kw in text:
            extracted_fields.append(ExtractedField(
                key="reservation_date",
                value=kw,
                confidence=0.7,
            ))
            break

    for time_match in re.finditer(r"\b(\d{1,2})\s*[h:](\d{2})?\b", text):
        hour = time_match.group(1)
        minute = time_match.group(2) or "00"
        extracted_fields.append(ExtractedField(
            key="reservation_time",
            value=f"{hour}:{minute}",
            confidence=0.85,
        ))
        break

    # Handoff detection (5 critical keywords)
    handoff_keywords = ["atendente", "humano", "pessoa real", "falar com alguém", "pessoa de verdade"]
    if any(kw in text for kw in handoff_keywords):
        handoff = True
        handoff_reason = "Cliente pediu humano"

    # Intent detection (best effort, low confidence)
    for intent in profile.conversation.primary_intents:
        if intent.lower() in text:
            detected_intent = intent
            break

    return ExtractedLeadData(
        detected_intent=detected_intent,
        intent_confidence=0.5 if detected_intent else 0.0,
        extracted_fields=extracted_fields,
        should_handoff=handoff,
        handoff_reason=handoff_reason,
        notes=["heuristic_fallback"],
    )