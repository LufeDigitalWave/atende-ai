# Phase 3 Report — Namespace Isolation + Onboarding

## Summary

Phase 3 adds tenant isolation to the RAG system, a CLI for knowledge base ingestion, an onboarding runbook with timed steps, and conditional Langfuse tracing.

## Changes

| File | Type | Description |
| --- | --- | --- |
| `backend/app/models/knowledge.py` | modified | Added `namespace` column (varchar 100, default 'default') |
| `backend/alembic/versions/0006_knowledge_namespace.py` | new | Migration: add namespace, replace unique index |
| `backend/app/services/retriever.py` | modified | Filter by namespace in both PgvectorRetriever and TsvectorRetriever |
| `backend/app/api/routes_chat.py` | modified | Pass session niche as namespace to retriever |
| `backend/app/cli/__init__.py` | new | CLI package init |
| `backend/app/cli/ingest.py` | new | Idempotent ingestion CLI by namespace |
| `backend/app/services/tracing.py` | new | Conditional Langfuse tracing (no-op when not configured) |
| `docs/ONBOARDING_RUNBOOK.md` | new | Timed onboarding steps from contract to go-live |
| `tests/guardrails/test_namespace_isolation.py` | new | Isolation test: tenant A cannot read tenant B |

## Test results

| Suite | Result |
| --- | --- |
| Backend pytest | 115 passed, 9 xfailed |
| Frontend unit | 7 passed |
| Frontend E2E | 20 passed |
| Guardrails | 36 passed (includes 4 new namespace tests) |
| Golden conversations | 10 passed |
| Protected paths diff | empty |

## Guardrail check

| Guardrail | Expected | Observed | Verdict |
| --- | --- | --- | --- |
| Namespace isolation | tenant A cannot read B | params include ns filter | PASS |
| KnowledgeChunk.namespace default | 'default' | verified in model | PASS |
| Retriever SQL includes namespace | WHERE namespace = :ns | verified in tsvector | PASS |
| All previous guardrails | pass | 32 + 4 new = 36 | PASS |

## Cost impact

- Before: R$ 0.02-0.05/conversation (SDR), R$ 0.01-0.03 (FAQ/RAG)
- After: same (namespace is a filter operation, no new LLM calls)
- Reason: namespace adds a WHERE clause to existing queries; zero token impact

## Pending

- Langfuse requires LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY in production env
- Backup automation not implemented (documented in runbook as manual)
- Restore drill not executed (requires staging environment)
- First real pilot not yet done (technical prerequisites complete)

## Recommendation for next phase

Phase 4 (LGPD + terms + unit economics) should wait until after the first real pilot, because:

1. Unit economics require Langfuse data from production conversations.
2. LGPD terms need legal review (cannot be auto-generated).
3. The first pilot will validate the onboarding runbook timing.

Recommended next action: close the first Starter pilot using the onboarding runbook, then start Phase 4 with real data.
