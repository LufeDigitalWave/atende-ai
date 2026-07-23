# Atende AI

**Agente SDR de IA que qualifica leads em tempo real — com CRM ao vivo.**

[![CI](https://github.com/LufeDigitalWave/atende-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/LufeDigitalWave/atende-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

`FastAPI` · `React` · `Claude/OpenAI` · `pgvector` · `SSE` · `Docker`

---

### 🎯 O que é

Uma demo pública que mostra um agente SDR de IA conversando com visitantes, extraindo dados estruturados e qualificando leads em tempo real — tudo visível num mini-CRM ao lado.

**30+ nichos** suportados. Escolha seu ramo (restaurante, clínica, imobiliária, advocacia...) e veja a IA se adaptar instantaneamente.

### ⚡ Teste em 60 segundos

```bash
git clone https://github.com/<ORG>/atende-ai.git
cd atende-ai
cp .env.example .env
docker compose up
```

Abra **http://localhost:5173**, escolha um nicho, envie "oi" e observe:
- O agente responde em streaming (token por token)
- O CRM ao lado preenche nome, interesse, score
- O funil avança de "Novo" → "Qualificando" → "Qualificado"
- Após 4 mensagens, aparece o CTA de conversão

> 💡 Funciona 100% offline com `FakeLLMProvider`. Com API key, usa LLM real.

---

### 🏗️ Arquitetura (3 Layers)

```
Layer 1: Factory (gpt-4.1-mini) → gera perfil da empresa fictícia por nicho
Layer 2: Renderer (determinístico) → preenche template de prompt fixo
Layer 3: Runtime (Claude/OpenAI SSE) → chat + extração + scoring + FSM
```

**Diferencial:** adicionar um nicho = zero código. A Factory gera dados; o template é fixo.

### 🛡️ 7 Guardrails de custo

| # | Guardrail | Config |
|---|-----------|--------|
| 1 | Cap por sessão | 30 msgs max |
| 2 | Rate limit | 2s entre msgs + 50 sessions/IP/h |
| 3 | Budget diário | 200k tokens (alerting webhook) |
| 4 | Input max | 500 chars |
| 5 | Session TTL | 24h (soft delete) |
| 6 | Kill switch | Admin toggle sem restart |
| 7 | Reset noturno | Cron container (soft delete + reseed) |

### 📊 O que a demo mostra

- **Chat SSE** com streaming real (typing indicator, markdown render)
- **CRM ao vivo** (lead profile, score explicável, funil, timeline)
- **Admin** com JWT auth, kanban de leads, dashboard de custos
- **30+ nichos** gerados dinamicamente (factory v3)
- **Scoring contextual** por nicho (restaurante pontua por reserva, B2B por urgência)
- **Handoff automático** quando lead está qualificado

### 🧪 Qualidade

- **124 testes** (backend pytest + vitest frontend)
- **CI** GitHub Actions (ruff + pytest + build + vitest)
- **Segurança:** SQL injection fix, security headers, PII sanitizer, fail-fast secrets
- **Docs:** EVALUATION.md com 21 cenários, CONVERSATION_DESIGN.md, 3 ADRs

---

## Como rodar

### Modo offline (FakeLLMProvider — sem API key)

```bash
cp .env.example .env
docker compose up
```

Acesse:
- Demo: http://localhost:5173
- Admin: http://localhost:5173/admin (credenciais no `.env`)
- API: http://localhost:8000/api/health

### Modo real (com LLM)

```bash
cp .env.example .env
# Edite .env: LLM_PROVIDER=openai, OPENAI_API_KEY=sk-...
docker compose up
```

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Backend | FastAPI + SQLAlchemy async + Alembic |
| Frontend | React 18 + Vite + Tailwind + React Router |
| DB | PostgreSQL 16 + pgvector (HNSW) |
| LLM | Claude Haiku 4.5 / OpenAI gpt-4o-mini |
| Infra | Docker Compose + EasyPanel + Traefik |
| CI | GitHub Actions |

---

## Documentação

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — diagrama completo + fluxo
- [AGENT_PROMPT.md](docs/AGENT_PROMPT.md) — anatomia do prompt v3 (3 layers)
- [EVALUATION.md](docs/EVALUATION.md) — 21 cenários de teste + rubrica
- [CONVERSATION_DESIGN.md](docs/CONVERSATION_DESIGN.md) — princípios de conversa
- [DEMO.md](docs/DEMO.md) — roteiro de call comercial
- [COST_MODEL.md](docs/COST_MODEL.md) — estimativa de custo por conversa
- [API.md](docs/API.md) — endpoints + eventos SSE
- [DEPLOY.md](docs/DEPLOY.md) — deploy completo

---

## Licença

[MIT](LICENSE) — © 2026 Luiz Felipe

---

> Todos os dados (empresa, serviços, agenda, vendedores) são **100% fictícios**. A IA é a única parte real.
