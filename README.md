# Atende AI

> Demo pública de um agente SDR de IA qualificando leads — com mini-CRM ao vivo.
>
> Visite a demo, converse com a **Sofia** (SDR fictícia da **Clínica Renova**) e veja o card do lead preenchendo sozinho do lado direito.

**English Summary**: Public portfolio demo showing a real AI SDR agent qualifying leads in real time, with a live mini-CRM that updates as the conversation happens. Single command to run (`docker compose up`). The agent runs against the real Claude API by default (`claude-haiku-4-5` for cost), with a scripted `FakeLLMProvider` fallback so the whole demo works offline.

<!-- Demo GIF: gere com as instruções em docs/screenshots/README.md -->
<!-- ![demo preview](docs/demo.gif) -->

> 📸 **Demo visual em breve.** Instruções de captura em [`docs/screenshots/README.md`](docs/screenshots/README.md).

---

## O que esta demo mostra

1. **Agente SDR real** (Claude API) com prompt versionado, RAG sobre base de conhecimento fictícia, extração estruturada paralela e regras de guardrail (não inventa preço, não negocia, redireciona fora de escopo).
2. **Mini-CRM ao vivo** atualizado por Server-Sent Events: dados do lead, score explicável, funil e timeline aparecem em <1s após cada turno.
3. **Guarda-corpos de custo** completos: cap por sessão, rate limit, budget diário, truncagem de histórico, limite de input, TTL de 24h e reset noturno.
4. **Admin** com transcript, kanban de leads, dashboard de custo e versão do agente.
5. **Pronto pra Easypanel/Traefik** com `docker-compose.yml`.

> Todos os dados (empresa, serviços, agenda, vendedores) são **100% fictícios**. A IA é a única parte real.

---

## Como rodar

### Modo offline (FakeLLMProvider — sem API key)

```bash
cp .env.example .env
docker compose up
```

Acesse:
- Demo pública: <http://localhost:5173>
- API: <http://localhost:8000>
- Admin: <http://localhost:5173/admin> (login com `ADMIN_USERNAME` / `ADMIN_PASSWORD` do `.env`)

### Modo real (Claude API)

Edite o `.env`:

```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
AGENT_MODEL=claude-haiku-4-5
```

Reinicie `docker compose up`. O agent agora usa a API real da Anthropic com prompt caching no system prompt.

---

## Estrutura

```
atende-ai/
├── README.md                # este arquivo
├── CLAUDE.md                # convenções do projeto, versionamento de prompt, testes
├── PROPOSTA_SNIPPET.md      # 2 versões de proposta comercial
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── ARCHITECTURE.md      # mermaid: chat → agent loop → SSE → CRM
│   ├── AGENT_PROMPT.md      # anatomia do prompt + changelog
│   ├── DEMO.md ⭐           # roteiro de call + objeções
│   ├── API.md               # endpoints + eventos SSE
│   ├── DEPLOY.md            # Easypanel + Traefik + env
│   └── COST_MODEL.md        # estimativa por conversa e por dia
├── backend/
│   └── app/
│       ├── agent/           # Sofia prompt + loop + extraction + score
│       ├── api/             # FastAPI routes
│       ├── services/        # LLMProvider, retriever, budget
│       ├── models/          # SQLAlchemy models
│       ├── schemas/         # Pydantic
│       ├── seeds/           # knowledge base fictícia
│       └── tests/
└── frontend/
    └── src/
        ├── pages/           # / /admin /como-funciona
        ├── components/chat/ # chat UI
        ├── components/crm/  # live CRM
        ├── hooks/
        └── lib/
```

---

## Critérios de aceite

- `docker compose up` com `LLM_PROVIDER=fake` roda 100% offline e completa o funil com o CRM atualizando.
- Com `LLM_PROVIDER=claude`, a Sofia conversa natural em PT-BR, extrai campos e nunca inventa preço fora do RAG.
- Streaming visível + updates do CRM em <1s.
- 7 guarda-corpos de custo implementados e testados.
- pytest ≥ 12 testes verdes.
- UI impecável em 375px e 1440px; sem trade dress de WhatsApp.
- Zero credenciais no repo.

Veja o checklist completo em `CLAUDE.md`.

---

## Licença

MIT.
