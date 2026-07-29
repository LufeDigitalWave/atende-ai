# Phase 1 Report — Server-Side Funnel + Conversion

## Summary

Phase 1 instruments the public vitrine with server-side conversion tracking, adds CSV export for leads, and audits CTAs to ensure one primary per route.

## Changes

| File | Type | Description |
| --- | --- | --- |
| `backend/app/models/funnel_event.py` | new | FunnelEvent model (7 steps, no PII) |
| `backend/alembic/versions/0004_funnel_events.py` | new | Migration for funnel_events table |
| `backend/app/api/routes_funnel.py` | new | POST /api/events + GET /api/admin/funnel |
| `backend/app/api/routes_admin.py` | modified | Added GET /api/admin/leads/export (CSV) |
| `backend/app/main.py` | modified | Registered funnel router |
| `frontend/src/lib/funnel.ts` | new | Fire-and-forget tracking helper |
| `frontend/src/App.tsx` | modified | track view_landing |
| `frontend/src/pages/Demo.tsx` | modified | track start_demo |
| `frontend/src/pages/Pricing.tsx` | modified | track clicked_pricing |
| `frontend/src/components/chat/ChatWindow.tsx` | modified | track first_message + reached_qualified |
| `frontend/src/components/marketing/CTASection.tsx` | modified | track clicked_whatsapp |
| `docs/CTA_AUDIT.md` | new | 1 primary CTA per route documented |
| `tests/guardrails/test_funnel_endpoint.py` | new | 6 tests for funnel validation |

## Test results

| Suite | Result |
| --- | --- |
| Backend pytest | 115 passed, 9 xfailed |
| Frontend unit | 7 passed |
| Frontend E2E | 20 passed |
| Guardrails | 32 passed |
| Protected paths diff | empty |

## Cost impact

- Before: R$ 0.02-0.05/conversation
- After: same (tracking is fire-and-forget HTTP, no LLM calls)
- Reason: funnel events are simple DB inserts, ~0 cost

## Pending

- Lead capture in-chat deferred until first real pilot validates approach
- Follow-up automation deferred to post-pilot phase

## Recommendation for next phase

Phase 2 (FAQ/RAG) unlocks selling Pro packages by demonstrating RAG with client documents in calls.
