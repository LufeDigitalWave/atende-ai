# Atende AI

Vitrine publica da linha WhatsApp Agents (Lufe Digital Wave). Agente SDR conversa,
qualifica leads e atualiza CRM ao vivo. Em producao para cliente, mesma arquitetura
vira agente real no WhatsApp oficial.

## Stack e comandos

| Camada | Tecnologia | Diretorio |
| --- | --- | --- |
| Backend | FastAPI + SQLAlchemy async + Alembic + pgvector | `backend/` |
| Frontend | React 18 + Vite + Tailwind + React Router + Lucide | `frontend/` |
| DB | PostgreSQL 16 + pgvector (HNSW) | docker `atende_db` |
| CI | GitHub Actions: ruff, pytest, vite build, vitest | `.github/workflows/ci.yml` |

```bash
# Backend
cd backend
pip install -e ".[dev]"
ruff check .
pytest -v --tb=short
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run build
npm test            # vitest
npm run test:e2e    # playwright
npm run dev         # vite :5173

# Full stack
docker compose up -d
docker compose logs -f api
```

## Arquitetura (3 layers)

- **Layer 1 — Factory:** gera perfil ficticio por nicho (chamada LLM, cache 1h).
- **Layer 2 — Renderer:** preenche template de prompt (deterministico, sem LLM).
- **Layer 3 — Runtime:** chat SSE + RAG + extracao + scoring + FSM + handoff.

Factory gera dado de *demo*. Nunca alimenta caminho de cliente real.

## Guardrails operacionais

| Guardrail | Valor | Modulo |
| --- | --- | --- |
| Cap por sessao | 30 msgs | `routes_chat.py` |
| Rate limit msg | 2s entre msgs | `services/rate_limit.py` |
| Rate limit sessoes | 50/IP/h | `services/rate_limit.py` |
| Budget diario | 200k tokens | `services/budget.py` |
| Input max | 500 chars | `schemas/chat.py` |
| Session TTL | 24h soft delete | `services/reset.py` |
| Kill switch | admin toggle | `services/killswitch.py` |

## Custo por conversa

Atual: R$ 0,02-0,05 (Haiku/gpt-4o-mini, 8 turnos medios, com prompt caching).
Toda mudanca que afete tokens, chamadas ou contexto declara o novo custo.

## Convencoes

- Codigo e commits em ingles. Conteudo de usuario final em PT-BR.
- Endpoint novo nasce com rate limit, validacao, sanitizacao de PII em log e teste.
- Dependencia nova exige justificativa.
- Commit: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).

## Skills do projeto

- `/audit-phase0` — auditoria completa antes de mudanca.
- `/guardrail-check` — verifica guardrails ativos.
- `/ship-phase` — fecha fase do roadmap (suite + review + PR).
- `/commercial-numbers` — valida numeros em material de venda.
- `/llmops` — observabilidade, prompt management e evals.

## Caminhos protegidos

Arquivos sob `.claude/`, `tests/guardrails/` e os listados em
`.claude/protected-paths.txt` nao sao editaveis pelo agente.
