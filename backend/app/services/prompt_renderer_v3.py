"""Prompt Renderer v3 — renders NicheProfile into system prompt.

This is Layer 2 of the 3-layer architecture:
- Layer 1: Factory (NicheProfile JSON, validated)
- Layer 2: Renderer (this file, deterministic)
- Layer 3: Runtime (Loop that appends history + lead state + RAG)

The template is fixed; only DATA varies per niche. This means:
- The same prompt structure is used for restaurante, clínica, B2B...
- Only the {services_rendered}, {journeys_rendered}, {prohibited_behaviors}, etc change.
- A/B testing prompts is now a single-file change.
"""
from __future__ import annotations

from pathlib import Path

from app.schemas.niche_profile import NicheProfile

TEMPLATE_PATH = Path(__file__).parent.parent / "agent" / "prompts" / "agent_template_v3.md"


# ============================================================
# Section renderers
# ============================================================

def _render_services(business) -> str:
    """Render services list like '- **Name**: 12x R$ X or R$ Y à vista (Duration) ⭐'."""
    lines = []
    for s in business.services:
        h = " ⭐" if s.highlight else ""
        if s.price_installments:
            price = f"{s.price_installments} ou {s.price_cash} à vista"
        else:
            price = s.price_cash
        lines.append(f"- **{s.name}**{h}: {price} ({s.duration_or_scope})")
    return "\n".join(lines)


def _render_faq(business) -> str:
    """Render FAQ like '- **Q?** — A'."""
    return "\n".join(f"- **{f.q}** — {f.a}" for f in business.faq)


def _render_journeys(conversation) -> str:
    """Render journeys with intent, goal, fields needed, and forbidden questions."""
    blocks = []
    for j in conversation.journeys:
        lines = [
            f"### {j.intent}",
            f"- **O que é:** {j.description}",
            f"- **Objetivo do agente:** {j.response_goal}",
            f"- **CTA sugerido:** {j.suggested_cta}",
        ]
        if j.qualification_fields:
            lines.append(
                f"- **Campos úteis:** {', '.join(j.qualification_fields)}"
            )
        if j.handoff_conditions:
            lines.append(
                f"- **Quando acionar handoff:** {', '.join(j.handoff_conditions)}"
            )
        if j.forbidden_questions:
            lines.append("- **NÃO pergunte:**")
            for fq in j.forbidden_questions:
                lines.append(f"  - {fq}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _render_qualification_fields(conversation) -> str:
    """Render qualification fields with their rules (when to ask, what's the purpose)."""
    lines = []
    for qf in conversation.qualification_fields:
        hint = ""
        if qf.required_for:
            hint = f" (obrigatório pra: {', '.join(qf.required_for)})"
        priority = f" [prioridade: {qf.priority}]"
        ask_only = " [só quando relevante]" if qf.ask_only_when_relevant else ""
        lines.append(
            f"- **{qf.label}** ({qf.key}){priority}{ask_only}{hint}\n"
            f"  Propósito: {qf.purpose}"
        )
    return "\n".join(lines)


def _render_prohibited_behaviors(conversation) -> str:
    return "\n".join(f"- {b}" for b in conversation.prohibited_behaviors)


def _render_objections(business) -> str:
    return "\n".join(f"- \"{o.objection}\" → {o.guideline}" for o in business.common_objections)


def _render_handoff_rules(conversation) -> str:
    """Conditional handoff — the agent triggers based on rules."""
    return "\n".join(f"- {r}" for r in conversation.handoff_rules)


# ============================================================
# Main renderer
# ============================================================

def render_prompt(profile: NicheProfile) -> str:
    """Render the agent_template_v3.md with the NicheProfile data.

    Returns the final system prompt string. Safe to ship to the LLM.
    """
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    business = profile.business
    conv = profile.conversation

    sections = {
        "{agent_name}": business.agent_name,
        "{company_name}": business.company_name,
        "{city}": business.city,
        "{tagline}": business.tagline,
        "{tone_notes}": business.tone_notes,
        "{services_rendered}": _render_services(business),
        "{faq_rendered}": _render_faq(business),
        "{journeys_rendered}": _render_journeys(conv),
        "{qualification_fields_rendered}": _render_qualification_fields(conv),
        "{prohibited_behaviors_rendered}": _render_prohibited_behaviors(conv),
        "{proactive_opening_strategy}": conv.proactive_opening_strategy,
        "{objections_rendered}": _render_objections(business),
        "{handoff_rules_rendered}": _render_handoff_rules(conv),
    }

    result = template
    for placeholder, value in sections.items():
        result = result.replace(placeholder, value)

    # Catch any remaining template vars (safety)
    import re
    leftover = re.findall(r"\{[a-z_]+\}", result)
    if leftover:
        import structlog
        logger = structlog.get_logger("prompt_renderer_v3")
        logger.warning(f"unfilled template placeholders: {leftover}")

    return result