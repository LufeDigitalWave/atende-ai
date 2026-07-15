# Security Policy — Atende AI

## Reporting a vulnerability

If you find a security issue in this project, please report it privately:

- **Email:** luiz23.lfsc@gmail.com
- **Subject:** `[SECURITY] Atende AI — <brief description>`

I'll acknowledge receipt within 48 hours and provide a timeline for a fix.

**Please do NOT open a public issue for security vulnerabilities.**

---

## What is fictitious

Everything in this demo is **100% fictitious** except the AI engine:

- "Clínica Renova", "PetVida", and all generated companies are invented.
- Names, addresses, phone numbers, and prices are fake.
- The knowledge base (RAG) contains fabricated content for demonstration purposes.
- Lead data collected during conversations is synthetic and ephemeral.

---

## Session data policy

| Aspect | Policy |
|---|---|
| Storage | PostgreSQL on a private VPS (no third-party analytics) |
| Retention | **24 hours max** — automatic purge at 03:00 BRT daily |
| PII handling | Visitor IPs are SHA-256 hashed with a server-side salt before storage; raw IPs are never persisted |
| Conversation logs | Deleted with the session (24h TTL) |
| Admin access | Password-protected (bcrypt + JWT), rate-limited login |
| LLM provider | Messages are sent to the configured LLM API (OpenAI / Anthropic) under their respective data policies; no fine-tuning or training occurs on user inputs |

---

## Guardrails

The demo implements 7 cost/abuse guardrails:

1. **30 messages/session cap** — prevents runaway conversations
2. **Rate limit** — 1 msg/2s per session, 5 new sessions/IP/hour
3. **Daily token budget** — global cap; banner shown when exceeded
4. **Input length limit** — 500 chars max per message
5. **Session TTL** — 24h, then expired
6. **Nightly reset** — all sessions/leads/messages purged at 03:00
7. **Prompt injection resistance** — niche input sanitized (60 char max, no line breaks); agent template is fixed and not user-controllable

---

## Responsible disclosure

This is a portfolio/demo project. If you discover that:
- A secret was accidentally committed → email me immediately
- The agent can be jailbroken → I appreciate the report but this is a demo, not a production system
- Data persists beyond 24h → that's a bug; please report

Thank you for helping keep this project safe.
