# Atende AI Backend

> FastAPI + Postgres + pgvector + Claude / FakeLLM

## Setup

### Local development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp ../.env.example ../.env
# Edit .env with your settings

# Run migrations and seed
alembic upgrade head
python -m app.seeds.knowledge
python -m app.seeds.admin

# Start dev server
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
cd ..
docker compose up
```

## Project structure

```
app/
├── core/              # Config, DB, logging, security, IP hashing
├── models/            # SQLAlchemy 2.0 ORM (7 tables)
├── schemas/           # Pydantic v2 request/response
├── agent/             # Sofia prompt, loop, extraction, scoring, states
├── services/          # LLMProvider, Retriever, Budget, RateLimit, Embedder
├── api/               # Routes: chat, admin, meta (SSE streaming)
├── seeds/             # Knowledge base (.md files) + admin seeder
└── tests/             # pytest suite (≥12 tests)
```

## Database

- **PostgreSQL 16 + pgvector** for embeddings
- **Alembic** for migrations
- **SQLAlchemy 2.0 async** ORM
- 7 tables: `sessions`, `messages`, `leads`, `lead_events`, `knowledge_chunks`, `usage_log`, `admin_users`

Migrations run automatically on startup (docker-compose).

## Seeding

Two seeders:

1. **Knowledge base** (`python -m app.seeds.knowledge`)
   - Loads 12 `.md` files from `seeds/knowledge/`
   - Chunks by 500 chars with 50-char overlap
   - Embeds via Voyage API or fake hash (deterministic)
   - Inserts into `knowledge_chunks` with pgvector + tsvector fallback

2. **Admin user** (`python -m app.seeds.admin`)
   - Creates default admin from `ADMIN_USERNAME` / `ADMIN_PASSWORD` env
   - Hashes password with bcrypt

Both are idempotent (safe to re-run).

## Configuration

Loaded from `.env` via Pydantic `Settings`:

- `LLM_PROVIDER`: `fake` (roteirizado offline) or `claude` (Anthropic API)
- `ANTHROPIC_API_KEY`: required if `LLM_PROVIDER=claude`
- `EMBEDDING_PROVIDER`: `fake` (hash) or `voyage`
- `DAILY_TOKEN_BUDGET`: cap em tokens/dia (~R$ 5 default)
- `ADMIN_USERNAME`, `ADMIN_PASSWORD`: credentials
- `JWT_SECRET`: sign tokens (deve ser longo e aleatório em prod)

## Testing

```bash
pytest -v
pytest --cov=app
pytest tests/test_scoring.py -v
```

Tests use `FakeLLMProvider` (offline), SQLite in-memory, and FakeEmbedder.

## API endpoints (passo 3)

- `GET /api/health` — healthcheck
- `POST /api/sessions` — criar sessão
- `GET /api/sessions/{id}` — estado atual
- `POST /api/sessions/{id}/messages` — enviar mensagem (SSE stream)
- `GET /api/sessions/{id}/events` — conectar só no SSE
- `POST /api/admin/login` — JWT login
- `GET /api/admin/conversas` — listar sessões
- `GET /api/admin/leads` — kanban
- `GET /api/admin/custos` — dashboard de custo
- `GET /api/admin/agente` — versão do prompt + config

## Providers (passo 3)

### LLMProvider ABC

- `ClaudeProvider`: streaming + prompt caching + usage_log
- `FakeLLMProvider`: regex-based roteirizado por estado

### Retriever ABC

- `PgvectorRetriever`: similarity search via pgvector
- `TsvectorRetriever`: fallback full-text search (sem embedding)

### Embedder ABC

- `VoyageEmbedder`: Voyage API
- `FakeEmbedder`: MD5 hash determinístico

## Next steps

1. ✅ Passo 1: Scaffold + docs + docker-compose
2. ✅ Passo 2: Models + migrations + seed
3. ⏭️ Passo 3: LLMProvider + agent loop + extraction + score + SSE
4. ⏭️ Passo 4: ClaudeProvider + retriever + guards
5. ⏭️ Passo 5: Frontend chat
6. ⏭️ Passo 6: Frontend CRM + /como-funciona
7. ⏭️ Passo 7: Admin routes
8. ✅ Passo 8: Docs
9. ⏭️ Passo 9: Final review
