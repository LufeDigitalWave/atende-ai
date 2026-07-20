# Atende AI — Convenções do Projeto

> Item de portfólio público. Tudo aqui é fictício **exceto** a IA (Claude API).
> Última atualização: 2026-07-20 (Sprint 0-5 — segurança, admin, CI, alerting, kill switch).

## Filosofia

1. **Demo pública = produto.** Tudo o que aparece aqui, o cliente da proposta vai abrir e clicar. Não dá pra esconder placeholder ou "TODO".
2. **Custo é produto.** Como o agente usa LLM real, cada chamada tem custo. Todos os 7 guarda-corpos do `README.md` são **requisito**, não nice-to-have.
3. **Faker primeiro.** Tudo que pode funcionar com `FakeLLMProvider` (roteirizado) deve funcionar — pra demo offline, pra testes e pra debug de fluxo sem gastar API.
4. **Dados ≠ prompt.** v3 introduz a separação em **3 layers** (Factory → Renderer → Runtime). Regras vivem em templates versionados; nichos só geram dados.
5. **Qualificação é contextual, não universal.** v3 aboliu os "5 campos universais". Cada nicho tem sua própria lista de campos (`ConversationProfile.qualification_fields`).
6. **Versão por camada.** Mudou template/prompt → bump de versão + changelog. Mudou schema → bump de versão + teste novo.
7. **Commit por etapa concluída.** Conventional Commits. Nada de WIP no main.
8. **Código/docs em inglês; UI/conteúdo em PT-BR.** (Padrão dos meus projetos.)
9. **Fail-fast em provider.** Se `LLM_PROVIDER=claude` sem `ANTHROPIC_API_KEY`, recusa na inicialização. Idem `embedding=voyage` sem `VOYAGE_API_KEY`.

---

## Arquitetura v3 — 3 layers

A evolução v3 separou o pipeline em três camadas isoláveis:

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: FACTORY (data-only)                                │
│ nichos → meta-prompt (factory_v3.md)                        │
│       → gpt-4.1-mini → JSON                                 │
│       → Pydantic validation                                 │
│       → NicheProfile (Business + Conversation)               │
│       → cache 1h                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: RENDERER (template fixo, versionado)               │
│ agent_template_v3.md + NicheProfile → system_prompt         │
│ - 1 template, todos os nichos renderizam aqui               │
│ - placeholders seguros ({agent_name}, {services_rendered})   │
│ - valida placeholders residuais (warning se sobrar)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: RUNTIME (loop, extract, score, state)              │
│ - retrieve (RAG) → chat (LLM) → extract (LLM tool use)       │
│ - score (contextual) → state (FSM)                          │
│ - SSE events                                                │
│ - fallback heurístico se LLM falhar                         │
└─────────────────────────────────────────────────────────────┘
```

### O que isso destrava

- **Adicionar nicho = só dados.** Não tem mais 1 prompt por nicho (v2 era
  assim). O `ConversationProfile` carrega intenções, jornadas, campos e
  regras.
- **A/B test de prompt = 1 arquivo.** Mudou
  `agent_template_v3.md` → bump de versão + changelog.
- **Regras auditáveis.** `prohibited_behaviors` é uma lista no perfil,
  renderizada como seção do prompt. Lê-se, valida-se, testa-se.
- **Scoring alinhado ao nicho.** Restaurante pontua por
  `party_size+date+time+name`; B2B pontua por `problem+urgency+decisor`.
  Sem 5 campos universais.
- **Extractor guiado.** LLM tool use recebe `allowed_keys` do perfil →
  não extrai o que não deve.

---

## Estrutura de pastas

```
backend/app/
├── agent/
│   ├── prompts/
│   │   ├── agent_template_v3.md        # template imutável (renderer)
│   │   ├── factory_v3.md               # meta-prompt (factory → LLM)
│   │   ├── sofia_v1.md                 # legacy v1 (não usar)
│   │   └── agent_template_v2.md        # legacy v2 (não usar)
│   └── loop.py                         # orquestra um turno (legacy v2)
├── api/
│   ├── routes_chat.py                  # POST /api/sessions, /messages (v3 SSE)
│   ├── routes_admin.py                 # /admin/* (login JWT)
│   └── routes_meta.py                  # /api/health, /api/info
├── services/
│   ├── llm.py                          # LLMProvider ABC + Claude/OpenAI/Fake
│   ├── retriever.py                    # RAG (pgvector ou tsvector)
│   ├── prompt_factory_v3.py            # Layer 1: factory (NicheProfile)
│   ├── prompt_renderer_v3.py           # Layer 2: render template
│   ├── lead_extractor.py               # Layer 3: extract LLM tool use + heuristic
│   ├── lead_scoring_v3.py              # Layer 3: scoring contextual por nicho
│   ├── budget.py                       # cap diário + usage_log
│   ├── rate_limit.py                   # middleware in-memory
│   ├── embedder.py                     # Embedder ABC + Voyage + Fake
│   └── reset.py                        # cron 03h
├── schemas/
│   ├── business_profile.py             # Layer 1: dados da empresa
│   ├── conversation_profile.py         # Layer 1: comportamento por nicho
│   ├── niche_profile.py                # Layer 1: Business + Conversation
│   └── lead_extraction.py              # Layer 3: ExtractedLeadData
├── models/                             # SQLAlchemy 2.0 async
├── seeds/knowledge/                    # 10–15 .md fictícios (legacy)
└── tests/                              # pytest + pytest-asyncio
```

---

## ConversationProfile — o coração da v3

Diferente do v2, **cada nicho tem ConversationProfile próprio**:

### Campos essenciais

- `business_mode`: enum (`reservation_based`, `appointment_based`,
  `consultative`, `transactional`, `mixed`).
- `primary_intents`: 3–8 intenções do nicho.
- `journeys`: lista de `ConversationJourney` (1–6), cada um com:
  - `intent`, `description`, `response_goal`, `suggested_cta`,
  - `qualification_fields` (referências a `QualificationField.key`),
  - `handoff_conditions` (lista de strings concretas),
  - `forbidden_questions` (proibições desta jornada).
- `qualification_fields`: 2–6 campos com regras:
  - `key` (camelCase), `label`, `purpose`,
  - `required_for` (lista de intents),
  - `priority` (high/medium/low),
  - `ask_only_when_relevant` (default True),
  - `prohibited_before_intent` (True para campos sensíveis como `budget`).
- `prohibited_behaviors`: 1–8 comportamentos proibidos.
- `handoff_rules`: 1–6 condições de handoff.
- `lead_scoring_rules`: dicionário de eventos → pontos (opcional).
- `proactive_opening_strategy`: parágrafo de abertura (sem "como posso
  ajudar?").
- `response_before_qualification`: **sempre True** — responda antes de
  pedir.
- `max_questions_per_message`: **sempre 1** (e quase nunca 2).

### Regras por business_mode (factory_v3.md documenta)

- **`reservation_based`** (restaurante): campos `customer_name,
  party_size, reservation_date, reservation_time`. **Nunca** incluir
  `budget_range`.
- **`appointment_based`** (clínica, salão): campos `customer_name, need,
  urgency, availability`. **Nunca** prometer resultado.
- **`consultative`** (B2B): campos `problem_type, urgency,
  decision_maker, budget (gradual)`. Orçamento é **gradual**, nunca
  primeira pergunta.
- **`transactional`** (delivery, e-commerce): campos `product_interest,
  delivery_zone, payment_preference`. Sem qualificação agressiva.
- **`mixed`** (academia, loja física): combina os anteriores.

---

## Factory (Layer 1) — `prompt_factory_v3.py`

### Sanitização de nicho

```python
def sanitize_niche(niche: str) -> str:
    """Anti prompt-injection via input do usuário."""
    cleaned = re.sub(r"[\n\r\t\x00-\x1f]", " ", niche)  # remove \n, \r, \t
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned[:60]                                    # max 60 chars
    if len(cleaned) < 3:
        cleaned = "consultoria empresarial"
    return cleaned
```

Nicho input → cache (TTL 1h) → LLM call → Pydantic validate →
NicheProfile. Falha → fallback estático (Sofia/Clínica Renova).

### Cache

- Chave: `niche.lower().strip()`.
- TTL: 1h.
- Invalidação: `clear_cache()` (chamado pelo `services/reset.py`
  durante reset noturno).

### Modelo

`factory_model` (env, default `gpt-4.1-mini`). Custo marginal: ~600
tokens por geração, ~R$ 0,001 por nicho novo. Pagos apenas na primeira
execução — depois cache.

---

## Renderer (Layer 2) — `prompt_renderer_v3.py`

Template: `backend/app/agent/prompts/agent_template_v3.md`.

Placeholders:

- `{agent_name}`, `{company_name}`, `{city}`, `{tagline}`, `{tone_notes}`
- `{services_rendered}` — lista com preços formatados
- `{faq_rendered}` — FAQ renderizado
- `{journeys_rendered}` — jornadas com `###` headings
- `{qualification_fields_rendered}` — campos com prioridade
- `{prohibited_behaviors_rendered}`, `{objections_rendered}`,
  `{handoff_rules_rendered}`
- `{proactive_opening_strategy}`

Validação automática: se sobrar placeholder `{...}` no output, log
warning `unfilled template placeholders`.

---

## Extrator (Layer 3) — `lead_extractor.py`

### LLM tool use (primary)

```python
EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_lead_data",
        "parameters": { ... }  # OpenAI JSON schema
    }
}
```

- `tool_choice: forced` (sempre chama).
- `temperature=0.1` (output estável).
- `max_tokens=500`.
- Filtro de keys: só passa `extracted_fields[].key` que existem em
  `ConversationProfile.qualification_fields`.
- Erro LLM → `notes=["heuristic_fallback"]`.

### Heurística (fallback)

Em `lead_extractor.py:_heuristic_fallback()`:

- Nome: `meu nome é X` ou repetido pelo agente.
- `party_size`: `N pessoas`, `somos N`.
- `reservation_date`: `hoje/amanhã/sábado`.
- `reservation_time`: regex `(\d{1,2})[h:](\d{2})?`.
- Handoff: 5 keywords (`atendente`, `humano`, `pessoa real`, `falar com
  alguém`, `pessoa de verdade`).
- Intenção: substring em `primary_intents`.

### Merge (LLM + heurístico)

`routes_chat.py` chama LLM, depois heurístico, e **adiciona** campos que
o LLM perdeu (heurístico nunca sobrescreve LLM).

---

## Scoring (Layer 3) — `lead_scoring_v3.py`

### Não-universal

```python
# Restaurante (exemplo):
lead_scoring_rules = {
    "intent_detected": 10,
    "name_informed": 10,
    "party_size_informed": 15,
    "date_informed": 15,
    "time_informed": 15,
}
```

```python
# Clínica:
lead_scoring_rules = {
    "intent_detected": 10,
    "need_informed": 20,
    "urgency_informed": 15,
    "availability_informed": 15,
}
```

### Cap 100

A pontuação é somada e capped em 100 via `min(breakdown.total, 100)`.
Handoff **não** soma ponto (é transição de estado, não score).

### Cumulatividade

`routes_chat.py:_build_cumulative_extraction()` reconstrói
`ExtractedLeadData` combinando:

- Campos extraídos no turno atual (via `extractor`).
- Campos já preenchidos em turns anteriores (via `lead.name`,
  `lead.service_interest`, etc).

Sem cumulatividade, o lead perde pontos após cada turno.

### Legacy

`compute_score_legacy()` (5-field, hardcoded) preservada como
fallback se `NicheProfile` indisponível. Não é usada em fluxo v3.

---

## Como rodar testes

```bash
cd backend
uv sync                              # ou pip install -r requirements.txt
pytest -v                            # tudo
pytest tests/test_factory_v3.py -v  # factory v3
pytest tests/test_lead_extractor.py -v  # extrator LLM
pytest tests/test_lead_scoring_v3.py -v # scoring v3
pytest --cov=app                     # com cobertura
```

Testes não tocam rede. `FakeLLMProvider` + SQLite em memória +
`AsyncMock` para OpenAI.

---

## Como versionar prompt

### Layer 1 (factory_v3.md ou data gerada)

- `factory_v3.md` mudou → bump versão no frontmatter + changelog em
  `docs/AGENT_PROMPT.md`.
- Schema de `BusinessProfile` mudou → bump major em
  `ConversationProfile` schema, **NÃO** muda código de
  `prompt_factory_v3.py` (esse arquivo só lê o schema).

### Layer 2 (agent_template_v3.md)

- Regras mudaram → bump versão `v3.x` no frontmatter + changelog.
- Variável nova no template → adicionar em `prompt_renderer_v3.py` e
  teste em `test_prompt_renderer_v3.py:test_no_unfilled_placeholders`.

### Layer 3 (extractor, scoring)

- Mudança em `lead_extractor.py` → adicionar teste + atualizar
  `docs/adr/ADR-003-structured-lead-extraction.md` se for decisão
  arquitetural.
- Mudança em `lead_scoring_v3.py` → adicionar cenário em
  `docs/EVALUATION.md` + medir correlação pós-deploy.

---

## Budget diário

- `DAILY_TOKEN_BUDGET` (default `200000`) = cap aproximado em tokens in/out combinados.
- Ao estourar, banner aparece na UI ("demo em alta demanda") + link `CONTACT_URL` (env).
- Conta em `usage_log` (por chamada: model, tokens, cached_tokens, cost_usd).
- Reset à meia-noite (timezone do servidor).

v3 adiciona **1 chamada extra por turno** (extractor LLM), ~600
tokens input + 80 output. Com `claude-haiku-4-5` no chat e `gpt-4.1-mini`
no extractor/factory, custo por conversa qualificada continua em
**R$ 0,03–0,08**.

Não altere o threshold sem avisar — demo pública pode estourar se
viralizar.

---

## Reset noturno (cron)

`backend/app/services/reset.py` é o job que às 03h local:

1. Apaga `sessions` com `last_activity_at < now() - 24h`.
2. Apaga `messages`, `leads`, `lead_events`, `usage_log` órfãos.
3. Re-rodada o seed da knowledge base (idempotente via `ON CONFLICT DO NOTHING`).
4. (v3) `clear_cache()` do `prompt_factory_v3` — invalida perfis.

No `docker-compose.yml`: `reset-cron` service roda em loop daily. Em
produção real, trocar por cron externo.

---

## Lint / format

```bash
# backend
cd backend
ruff check .
ruff format .

# frontend
cd frontend
npm run lint
npm run format
```

CI deve bloquear merge com lint vermelho.

---

## Commits

Conventional Commits. Exemplos:

```
feat(factory): add ConversationProfile template for pet shop
fix(extractor): filter disallowed keys when LLM returns extra
docs(eval): add 5 pet shop scenarios + scoring rules
test(scoring): add pet shop fixture to test_lead_scoring_v3
refactor(renderer): split renderer into 5 section renderers
chore(deps): bump anthropic-sdk to 0.42
perf(factory): cache profiles for 1h (already in main)
```

---

## Segurança / portfólio

- **Zero credenciais no repo.** Apenas `.env.example` comentado. Verifique com `grep -rE "sk-ant|sk-live|AKIA|ghp_" .` antes do commit.
- **LGPD:** IPs do visitante são hasheados (`ip_hash`, sha256 + salt), nunca raw.
- **Logs nunca contêm input do usuário** (a IA pode receber dado sensível).
- **Anti-injection nicho:** `sanitize_niche()` (max 60 chars, sem control chars).
- **Anti-injection mensagem:** cap 500 chars, 30 msgs/sessão, system
  prompt nunca exposto.
- **Admin:** bcrypt para senha, JWT 24h, rate limit em login (5 tentativas/15min).

---

## Quando travar (v3)

| Sintoma | Onde olhar |
|---|---|
| Sofia não atualiza CRM | `routes_chat.py:generate_sse()` + `lead_extractor.py` |
| Score=0 com lead cheio | `score_breakdown` no admin → `_field_to_scoring_event()` em `lead_scoring_v3.py` |
| Handoff não disparou | `extraction.should_handoff` (logs) + `ConversationProfile.handoff_rules` |
| Extractor sempre em fallback | `notes=["heuristic_fallback"]` nos logs → API key ou rate limit |
| Prompt renderizado com `{...}` vazio | `prompt_renderer_v3.py` warning `unfilled template placeholders` |
| Factory gerando perfil inválido | Pydantic em `prompt_factory_v3.py` → fallback estático deve ativar |
| Reset não roda | log do container `reset-cron`; checar TZ do container |
| Budget excedido | `usage_log` GROUP BY DATE; ver `docs/COST_MODEL.md` |
| Demo offline não completa funil | `FakeLLMProvider` em `services/llm.py` |

---

## Próximos passos depois do MVP

1. Multi-tenant (cada deploy = uma empresa).
2. Webhook real de handoff (não só registrar na timeline — mandar pra
   n8n/HubSpot real).
3. Áudio (transcrição + resposta em texto v1).
4. Painel admin para editar perfis sem redeploy.
5. Métricas reais (`correlation score>=50 ↔ handoff_produtivo`).

Nenhuma vai pro MVP — a regra é: demo tem que caber num `docker compose up`.

---

## Estado operacional (2026-07-20)

### Sprints entregues (0-5)

| Sprint | Foco | PR |
|---|---|---|
| 0 | SQL injection fix, fail-fast secrets, sofia-* palette, getState reativo, anonimização | #1 |
| 1 | Admin auth real, react-router, kanban funcional, mobile responsive | #1 |
| 2 | CI GitHub Actions, meta OG/twitter, security headers, PII sanitizer, vitest, LICENSE/CHANGELOG | #1 |
| 3 | Token logging (usage_log), budget alerting (webhook + Telegram), admin /custos real | #1 |
| 4 | HTTP integration tests (httpx AsyncClient, 16 testes chat+admin) | #2 |
| 5 | Kill switch operacional, soft delete (deleted_at), contact_url dinâmico | #3 |

### Guarda-corpos ativos

1. Rate limit per-session (2s) + per-IP (5 sessions/h)
2. Budget cap diário (200k tokens) com alerting
3. Message cap (30 msgs/sessão)
4. Input cap (500 chars)
5. Session TTL (24h) + soft-delete noturno
6. Kill switch (chat + handoff, admin toggle)
7. Fail-fast em segredos defaults em produção

### CI

- Backend: ruff + pytest (152 passed + 9 xfail SQLite)
- Frontend: vite build + vitest (7 passed)
- Trigger: push + PR para main

### Testes

- Backend: 161 testes (unitários + integração HTTP)
- Frontend: 7 testes (Zustand store)
- Integration tests marcados xfail em SQLite (passam em PostgreSQL CI)

### Produção (VPS 93.127.211.7 — NÃO atualizada)

Último deploy: 2026-07-16. As sprints 0-5 estão apenas no GitHub (main).
Para aplicar em prod: `git pull + docker compose build + docker compose up -d + alembic upgrade head`.

### Migration pendente em prod

- `0002_soft_delete.py` — adiciona `deleted_at` em sessions/leads.

---

## Documentação auxiliar (referência rápida)

- `docs/ARCHITECTURE.md` — diagrama e fluxo detalhado.
- `docs/CONVERSATION_DESIGN.md` — regras de conversa (atendimento
  natural, handoff, objeções).
- `docs/EVALUATION.md` — cenários de teste, rubrica, métricas.
- `docs/AGENT_PROMPT.md` — anatomia dos prompts + changelog.
- `docs/COST_MODEL.md` — estimativa de custo por conversa.
- `docs/ADR-001-conversation-profile.md` — decisão de
  ConversationProfile.
- `docs/ADR-002-contextual-lead-scoring.md` — decisão de scoring
  contextual.
- `docs/ADR-003-structured-lead-extraction.md` — decisão de extracção
  via LLM tool use.
- `docs/DEMO.md` — roteiro de call + objeções comerciais.
- `docs/API.md` — endpoints + eventos SSE.
- `docs/DEPLOY.md` / `docs/DEPLOY_VPS.md` — deploy dev/prod.
- `.claude/skills/conversation-design/SKILL.md` — guia de design de conversa.
- `.claude/skills/prompt-safety/SKILL.md` — checklist de segurança
  contra injection.
- `.claude/skills/quality-assurance/SKILL.md` — fluxo de QA + testes.
- `.claude/skills/feature-implementation/SKILL.md` — pipeline de
  feature nova.
