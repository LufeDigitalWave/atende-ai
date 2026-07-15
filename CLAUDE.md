# Atende AI — Convenções do Projeto

> Item de portfólio público. Tudo aqui é fictício **exceto** a IA (Claude API).
> Última atualização: 2026-07-15.

## Filosofia

1. **Demo pública = produto.** Tudo o que aparece aqui, o cliente da proposta vai abrir e clicar. Não dá pra esconder placeholder ou "TODO".
2. **Custo é produto.** Como o agente usa LLM real, cada chamada tem custo. Todos os 7 guarda-corpos do `README.md` são **requisito**, não nice-to-have.
3. **Faker primeiro.** Tudo que pode funcionar com `FakeLLMProvider` (roteirizado) deve funcionar — pra demo offline, pra testes e pra debug de fluxo sem gastar API.
4. **Prompt versionado.** O system prompt da Sofia é arquivo (`backend/app/agent/prompts/sofia_v1.md`), nunca string solta no código. Mudou → bump versão + changelog em `docs/AGENT_PROMPT.md`.
5. **Commit por etapa concluída.** Conventional Commits. Nada de WIP no main.
6. **Código/docs em inglês; UI/conteúdo em PT-BR.** (Padrão dos meus projetos.)
7. **Fail-fast em provider.** Se `LLM_PROVIDER=claude` sem `ANTHROPIC_API_KEY`, recusa na inicialização. Idem `embedding=voyage` sem `VOYAGE_API_KEY`.

---

## Estrutura de pastas

```
backend/app/
├── agent/
│   ├── prompts/
│   │   └── sofia_v1.md        # prompt da Sofia (versionado!)
│   ├── loop.py                # agent loop (turn -> LLM + extract + score + events)
│   ├── extractor.py           # extração estruturada (tool use / JSON)
│   ├── scoring.py             # score determinístico e explicável
│   └── states.py              # FSM: novo → em_qualificacao → qualificado → agendamento_proposto → handoff
├── api/
│   ├── routes_chat.py         # POST /api/sessions, POST /api/sessions/{id}/messages, GET .../events
│   ├── routes_admin.py        # /admin/* (login JWT)
│   └── routes_meta.py         # /api/health, /api/info
├── services/
│   ├── llm.py                 # LLMProvider ABC + ClaudeProvider + FakeLLMProvider
│   ├── retriever.py           # Retriever ABC + PgvectorRetriever + TsvectorRetriever
│   ├── budget.py              # cap diário + usage_log
│   ├── rate_limit.py          # middleware in-memory por session_id e IP
│   └── embedder.py            # Embedder ABC + VoyageEmbedder + FakeEmbedder
├── models/                    # SQLAlchemy 2.0 async
├── schemas/                   # Pydantic v2
├── seeds/
│   └── knowledge/             # 10–15 .md fictícios da Clínica Renova
└── tests/                     # pytest + pytest-asyncio
```

---

## Como rodar testes

```bash
cd backend
uv sync                              # ou pip install -r requirements.txt
pytest -v                            # roda tudo
pytest tests/test_scoring.py -v      # roda um arquivo
pytest --cov=app                     # com cobertura
```

Testes não tocam rede. `FakeLLMProvider` + SQLite em memória + FakeEmbedder (hash determinístico).

---

## Como versionar o prompt da Sofia

1. Edite `backend/app/agent/prompts/sofia_v1.md`.
2. Bump a versão no frontmatter (`version: 2`).
3. Adicione entrada em `docs/AGENT_PROMPT.md` no changelog.
4. Adicione 1 teste em `tests/test_prompt_version.py` confirmando que o loader retorna a versão esperada.
5. Rode a suíte. Mude o `AGENT_PROMPT_VERSION` no `.env` se quiser A/B.

**Nunca** edite o prompt direto no código. **Nunca** duplique string em testes — sempre carregar do arquivo.

---

## Budget diário

- `DAILY_TOKEN_BUDGET` (default `200000`) = cap aproximado em tokens in/out combinados.
- Ao estourar, banner aparece na UI ("demo em alta demanda") + link `CONTACT_URL` (env).
- Conta em `usage_log` (por chamada: model, tokens, cached_tokens, cost_usd).
- Reset à meia-noite (timezone do servidor).

Não altere o threshold sem avisar — demo pública pode estourar se viralizar.

---

## Reset noturno (cron)

`backend/app/services/reset.py` é o job que às 03h local:
1. Apaga `sessions` com `last_activity_at < now() - 24h`.
2. Apaga `messages`, `leads`, `lead_events`, `usage_log` órfãos.
3. Re-rodada o seed da knowledge base (idempotente via `ON CONFLICT DO NOTHING`).

No docker-compose: `reset-cron` service roda `python -m app.services.reset` em loop daily. Em produção real, trocar por cron externo.

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
feat(agent): add Sofia v2 prompt with stricter RAG injection
fix(crm): dedupe quick replies on slot pick
docs(demo): add objection handling for "AI inventa coisas?"
test(scoring): cover urgency bonus edge cases
chore(deps): bump anthropic-sdk to 0.42
```

---

## Segurança / portfólio

- **Zero credenciais no repo.** Apenas `.env.example` comentado. Verifique com `grep -rE "sk-ant|sk-live|AKIA|ghp_" .` antes do commit.
- **LGPD:** IPs do visitante são hasheados (`ip_hash`, sha256 + salt), nunca raw.
- **Logs nunca contêm input do usuário** (a Sofia pode receber dado sensível).
- **Admin**: bcrypt para senha, JWT 24h, rate limit em login (5 tentativas/15min).

---

## Quando travar

| Sintoma | Onde olhar |
|---|---|
| Sofia não atualiza CRM | `backend/app/agent/loop.py` + `services/llm.py` (extração retornou?) |
| SSE não conecta | `api/routes_chat.py` + CORS (`origins` em `main.py`) |
| Reset não roda | log do container `reset-cron`; checar TZ do container |
| Budget excedido | `usage_log` GROUP BY DATE; ver `docs/COST_MODEL.md` |
| Demo offline não completa funil | `FakeLLMProvider` em `services/llm.py` |

---

## Arquitetura — decisões da sessão 15/07

1. **Factory v2 (dados-não-prompt):** LLM gera BusinessProfile JSON → template fixo renderiza system prompt. Regras de batalha vivem no template versionado.
2. **Provider híbrido:** `gpt-4.1-mini` gera perfis (factory), `claude-haiku-4-5` conversa (agente). Prompt caching no system prompt (80% cache hit).
3. **Redesign dark premium:** canvas escuro azulado, gradiente violeta→ciano, device frame claro, micro-animações CSS.
4. **Sanitização:** niche input max 60 chars, sem line breaks, sem controle chars. Injection-safe.

---

## Próximos passos depois do MVP

1. A/B test de prompts (Sofia v1 vs v2 com mesmo lead).
2. Webhook de handoff (não só registrar na timeline — mandar pra n8n/HubSpot real).
3. Suporte a áudio (transcrição + resposta em texto na v1).
4. Painel multi-empresa (atendente configura nome da clínica, serviços, base RAG).

Nenhuma dessas vai pro MVP — a regra é: demo tem que caber num docker compose up.
