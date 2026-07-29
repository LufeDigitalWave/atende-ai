# Phase 2 Report — FAQ/RAG Agent Type

## Summary

Phase 2 introduces `agent_type` as a first-class concept, making the Runtime configurable for different agent behaviors without new code. The FAQ/RAG agent integrates the retriever into the chat loop and disables lead scoring.

## Changes

| File | Type | Description |
| --- | --- | --- |
| `backend/app/models/session.py` | modified | Added AgentType enum + agent_type/niche columns |
| `backend/app/models/__init__.py` | modified | Export AgentType |
| `backend/alembic/versions/0005_session_agent_type.py` | new | Migration for agent_type + niche on sessions |
| `backend/app/api/routes_chat.py` | modified | Accept agent_type, integrate RAG, conditional scoring |
| `backend/app/services/prompt_renderer_v3.py` | modified | Select template by agent_type |
| `backend/app/agent/prompts/agent_template_faq_rag.md` | new | Dedicated FAQ/RAG template |
| `docs/AGENT_SPEC.md` | new | Agent contract documentation |
| `tests/golden/test_faq_rag_golden.py` | new | 10 golden conversation tests |

## Test results

| Suite | Result |
| --- | --- |
| Backend pytest | 115 passed, 9 xfailed |
| Frontend unit | 7 passed |
| Frontend E2E | 20 passed |
| Guardrails | 32 passed |
| Golden conversations | 10 passed |
| Protected paths diff | empty |

## Cost impact

- SDR: R$ 0.02-0.05/conversation (unchanged)
- FAQ/RAG: R$ 0.01-0.03/conversation (cheaper — no extraction LLM call)
- Reason: FAQ/RAG skips lead_extractor call, saving ~50% of LLM cost per turn

## Pending

- Real-world validation with client PDF in call
- Langfuse tracing for measuring actual cost
- Eval metrics (fundamentação ≥90%, recusa ≥95%) require production traffic

## Recommendation for next phase

Phase 3 (namespace isolation + onboarding) is the prerequisite for deploying FAQ/RAG to a real client without data leakage.
