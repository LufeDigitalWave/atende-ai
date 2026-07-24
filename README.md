# Atende AI — WhatsApp Agents Demo

**Demo pública de agentes de IA para WhatsApp, começando por um SDR Agent que qualifica leads em tempo real com CRM ao vivo.**

[![CI](https://github.com/LufeDigitalWave/atende-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/LufeDigitalWave/atende-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

`FastAPI` · `React` · `Claude/OpenAI` · `PostgreSQL` · `pgvector` · `SSE` · `Docker`

---

## O que é

Atende AI é a vitrine principal da linha **WhatsApp Agents** da Lufe Digital Wave.

A demo mostra um agente SDR de IA conversando com visitantes, extraindo dados estruturados, qualificando leads e atualizando um mini-CRM ao vivo. Em produção, a mesma arquitetura pode operar pelo WhatsApp oficial da Meta, integrada com CRM, agenda, base de conhecimento, Chatwoot, n8n ou sistemas internos.

A linha WhatsApp Agents cobre seis ofertas:

1. **SDR Agent** — vendas e qualificação de leads.
2. **Support Agent** — atendimento e suporte 24/7.
3. **Appointment Agent** — agendamento automático.
4. **FAQ/RAG Agent** — respostas com base de conhecimento.
5. **Civic Agent** — atendimento público e protocolos.
6. **Collections Agent** — follow-up, reativação e cobrança leve.

---

## Teste em 60 segundos

```bash
git clone https://github.com/LufeDigitalWave/atende-ai.git
cd atende-ai
cp .env.example .env
docker compose up
```

Acesse:

- [Landing](http://localhost:5173)
- [Demo SDR](http://localhost:5173/demo)
- [Catálogo de agentes](http://localhost:5173/agentes)
- [API health](http://localhost:8000/api/health)

A interface administrativa existe para desenvolvimento local e operação interna; configure credenciais fortes no `.env` antes de expor qualquer ambiente.

Escolha um nicho, envie uma mensagem e observe:

- streaming de resposta token por token;
- extração de dados do lead;
- score e funil em tempo real;
- CRM visual preenchido durante a conversa;
- CTA comercial após interação suficiente.

> Funciona offline com `FakeLLMProvider`. Com API key, usa LLM real.

---

## Arquitetura em 3 layers

```text
Layer 1: Factory    → gera perfil de empresa fictícia por nicho
Layer 2: Renderer   → preenche template de prompt versionado
Layer 3: Runtime    → chat, RAG, extração, scoring, FSM e SSE
```

Diferencial: adicionar um nicho não exige criar um prompt novo manualmente. A Factory gera dados estruturados, o Renderer monta o prompt e o Runtime executa o atendimento.

---

## Guardrails operacionais

| Guardrail | Configuração |
| --- | --- |
| Cap por sessão | 30 mensagens no máximo |
| Rate limit | 2s entre mensagens + 50 sessões/IP/h |
| Budget diário | 200k tokens com alerting webhook |
| Input max | 500 caracteres por mensagem |
| Session TTL | 24h com soft delete |
| Kill switch | Toggle no admin sem restart |
| Reset noturno | Cron container para soft delete + reseed |

---

## O que a demo mostra

- Chat SSE com streaming real.
- CRM ao vivo com perfil, score, funil e timeline.
- Admin com JWT, kanban de leads e custos.
- Factory v3 por nicho.
- Scoring contextual.
- Handoff quando o lead está pronto.
- Sanitização de PII e dados fictícios para portfólio.

---

## Stack

| Camada | Tecnologia |
| --- | --- |
| Backend | FastAPI + SQLAlchemy async + Alembic |
| Frontend | React 18 + Vite + Tailwind + React Router |
| DB | PostgreSQL 16 + pgvector |
| LLM | Claude / OpenAI / Fake provider |
| Infra | Docker Compose + EasyPanel + Traefik |
| CI | GitHub Actions |

---

## Documentação

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — arquitetura e fluxo.
- [AGENT_PROMPT.md](docs/AGENT_PROMPT.md) — anatomia do prompt v3.
- [EVALUATION.md](docs/EVALUATION.md) — cenários de teste e rubrica.
- [CONVERSATION_DESIGN.md](docs/CONVERSATION_DESIGN.md) — princípios conversacionais.
- [DEMO.md](docs/DEMO.md) — roteiro de call comercial.
- [COST_MODEL.md](docs/COST_MODEL.md) — custo por conversa.
- [API.md](docs/API.md) — endpoints e eventos SSE.
- [DEPLOY.md](docs/DEPLOY.md) — deploy.

---

## Aviso de portfólio

Todos os dados de empresa, serviços, agenda, vendedores e leads são fictícios. A demo foi desenhada para portfólio público e não expõe dados de clientes reais.

---

## Licença

[MIT](LICENSE) — © 2026 Luiz Felipe
