# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Operational kill switch with admin toggle (GET/POST /api/admin/killswitch)
- Soft delete for sessions and leads (deleted_at column + Alembic migration 0002)
- Frontend contact_url from backend config (replaces hardcoded WhatsApp link)
- GitHub Actions CI (ruff + pytest + frontend build)
- Security headers (nginx + backend middleware)
- PII sanitizer in structlog pipeline
- Vitest setup for frontend testing
- Open Graph / Twitter Card meta tags
- LICENSE, CHANGELOG, CONTRIBUTING files
- HTTP integration tests for chat + admin routes (httpx AsyncClient)

### Changed

- reset.py now soft-deletes sessions instead of hard DELETE
- Handoff is suppressed when kill_switch_handoff=false

## [0.3.0] - 2026-07-20

### Fixed

- SQL injection in TsvectorRetriever (parameterized queries)
- Admin auth stub replaced with real JWT decode (HTTPBearer)
- Kanban admin endpoint now returns real lead data
- `useSessionStore.getState()` in JSX replaced with reactive selector
- Tailwind `sofia-*` palette defined (24 classes unblocked)
- DEPLOY_VPS.md anonymized (no real IP/domain/SSH)
- Count query fixed (`func.count()` instead of lambda)

### Added

- React Router with lazy routes (`/admin`, `/como-funciona`)
- Responsive mobile layout (CRM stacks below chat on small screens)
- Fail-fast validator for JWT_SECRET and ADMIN_PASSWORD defaults in production
- Security regression tests (`test_security_sprint0.py`)
- Demo capture instructions (`docs/screenshots/README.md`)
- `.superpowers/` and `docs/superpowers/` added to `.gitignore`

## [0.2.0] - 2026-07-16

### Added

- Factory v3 architecture (NicheProfile = BusinessProfile + ConversationProfile)
- Prompt renderer v3 (deterministic template substitution)
- LLM-based lead extractor with tool_use + heuristic fallback
- Contextual lead scoring v3 (per-niche qualification fields)
- ConversationProfile with journeys, handoff rules, prohibited behaviors
- 30 niches validated end-to-end
- Dark premium redesign (gradient violet→cyan, device frame)
- CRM dinâmico renderizado por ConversationProfile fields
- 3 ADRs (conversation-profile, contextual-scoring, structured-extraction)
- EVALUATION.md with 21 scenarios and 5-dimension rubric
- CONVERSATION_DESIGN.md

## [0.1.0] - 2026-07-10

### Added

- Initial MVP: FastAPI + React + PostgreSQL + pgvector
- Sofia v1 SDR agent with static prompt
- Basic chat with SSE streaming
- Simple 5-field lead extraction (heuristic)
- Rate limiting, budget caps, session TTL
- Admin login with bcrypt + JWT
- Docker Compose with EasyPanel/Traefik support
