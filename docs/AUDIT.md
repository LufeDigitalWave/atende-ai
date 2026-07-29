# Auditoria Fase 0 — Atende AI

**Data:** 2026-07-28  
**Método:** inspeção estática do repositório + execução de suíte + curl produção  
**Resultado:** 3 hipóteses confirmadas; 26 guardrails testados; 2 erros comerciais corrigidos  

---

## 1. Matriz dos 6 agentes vs Runtime real

| Agente | Status | Evidência | O que falta |
| --- | --- | --- | --- |
| SDR | implementado | `routes_chat.py:116-496` — factory v3, FSM, extração, scoring, handoff | Integrações reais CRM/WhatsApp |
| Support | só marketing | `agents.ts:36-44` — card sem runtime | Classificação, ticket, RAG por suporte, Chatwoot |
| Appointment | parcial | `conversation_profile.py:21` — `appointment_based` suportado; `lead.py:80` — `scheduled_slot` fictício | Agenda real, persistência de slot, lembretes |
| FAQ/RAG | parcial | `retriever.py:37-120` existe; `seeds/knowledge/` existe — mas retriever não integrado em `routes_chat.py` | Chamar retriever no loop, injetar chunks, política de resposta |
| Civic | só marketing | `agents.ts:69-77` — card sem runtime | Taxonomia, geocoding, protocolo, integração |
| Collections | só marketing | `agents.ts:80-88` — card sem runtime | Cadência ativa, opt-out, campanhas, templates Meta |

**Conclusão:** Runtime funcional é um SDR genérico por nicho. Appointment e FAQ/RAG têm peças reaproveitáveis mas não estão funcionais como produtos.

---

## 2. Fronteira demo × produção

### Mocks e fallbacks que vazam se operador não configurar

| Item | Arquivo | Vaza? | Consequência |
| --- | --- | --- | --- |
| `LLM_PROVIDER` default `fake` | `config.py:31` | sim | Chat responde com script Sofia/Clínica Renova |
| `EMBEDDING_PROVIDER` default `fake` | `config.py:43` | sim | RAG usa hash fake |
| Factory fallback Sofia | `prompt_factory_v3.py:44-132` | sim | Qualquer nicho vira clínica estética |
| `CONTACT_URL` placeholder | `config.py:23` | sim | CTA vai para número fictício |
| Seeds Clínica Renova | `seeds/knowledge/*.md` | sim | KB de demo em produção |
| `ADMIN_PASSWORD=admin` | `config.py:75` | sim* | *Só se `ENVIRONMENT != production` |
| `JWT_SECRET=change-me` | `config.py:76` | sim* | *Só se `ENVIRONMENT != production` |

### Fail-fast existente

- JWT/admin bloqueado em production: `config.py:105-125`, `main.py:63-71`
- Claude sem key bloqueado: `main.py:84-89`
- DB indisponível: `main.py:74-82`

### Fail-fast FALTANTE

- `LLM_PROVIDER=fake` em production não falha
- `EMBEDDING_PROVIDER=fake` em production não falha
- `CONTACT_URL` inválido não falha (cai para placeholder)
- `ENVIRONMENT` default é `development` — se esquecer, guards desligam

---

## 3. Generalização real

### O que a Factory abstrai

- Nicho de negócio (string → NicheProfile via LLM)
- BusinessMode: `transactional`, `appointment_based`, `reservation_based`, `consultative`, `mixed`
- ConversationProfile com jornadas, campos, handoff, scoring

### O que está hardcoded para SDR

- Factory recebe apenas `niche`, não `agent_type`
- Fallback é 100% SDR de clínica estética
- Meta-prompt é orientado a empresa fictícia com qualificação comercial
- Template único (`agent_template_v3.md`) com qualificação, objeções, handoff
- Renderer não seleciona template por agente
- Runtime não chama retriever; assume sempre lead extraction + scoring + FSM

### Gap para FAQ/RAG funcional

Mínimo 7 arquivos backend: `conversation_profile.py`, `prompt_factory_v3.py`, `prompt_renderer_v3.py`, `routes_chat.py`, `lead_scoring_v3.py`, `lead_extractor.py`, `states.py`. Implementação robusta: 9-10 arquivos + migration + frontend.

---

## 4. Cobertura por risco

| Risco | Status | Evidência |
| --- | --- | --- |
| SQL injection | PARCIAL | `test_security_sprint0.py:24-38` (retriever); `routes_chat.py` usa UUID validado |
| Autorização admin JWT | TESTADO | `test_routes_admin.py:42-99` (xfail SQLite) |
| Rate limit msg 2s | TESTADO | `tests/guardrails/test_rate_limit.py:15-31` |
| Rate limit 5 sessões/IP/h | TESTADO | `tests/guardrails/test_rate_limit.py:34-49` |
| Budget 200k tokens | NÃO TESTADO | Requer DB async |
| Input max 500 chars | TESTADO | `tests/guardrails/test_input_validation.py:8-25` |
| TTL 24h + soft delete | NÃO TESTADO | Requer DB async |
| Kill switch | PARCIAL | Serviço testado (`test_killswitch.py`); HTTP 503 não testado |
| PII em log | TESTADO | `test_pii_sanitizer.py:20-61` |
| Telefone real no bundle | TESTADO | `test_contact_url.py:20-31` |
| Security headers | TESTADO | `test_security_headers.py:38-44` (produção) |
| contact_url allowlist | NÃO TESTADO | Validator existe, sem teste |
| CORS | NÃO TESTADO | Middleware existe, sem teste |
| Open redirect | NÃO TESTADO | Sanitização frontend existe, sem teste |

---

## 5. Protected-paths.txt — bug e expansão

**Bug encontrado:** hook `protect-paths.sh` usa `case` sem `shopt -s globstar`; padrões `**` são literais e não casam subpastas. Corrigido nesta sessão.

**Expansão:** adicionados caminhos de auth, modelos PII, admin, migrations, deploy configs.

---

## 6. Dívida técnica por risco comercial

| Item | Risco | Esforço | Prioridade |
| --- | --- | ---: | --- |
| Multi-tenancy / isolamento | Alto — escalar exige refactor | 5-8 dias | P0 |
| Segundo agente FAQ/RAG | Alto — catálogo promete | 3-5 dias | P0 |
| Captura de lead / funil | Alto — vitrine não converte | 2-4 dias | P0 |
| Onboarding de cliente real | Alto — vender pilot exige | 2-3 dias | P0 |
| Backup testado | Médio-alto | 0,5-1,5 dia | P1 |
| Langfuse observability | Médio-alto | 1-2 dias | P1 |
| CORS testado | Médio | 0,5 dia | P1 |
| Fail-fast completo em prod | Médio-alto | 1 dia | P1 |
| SQLite xfail no CI | Médio | 1-2 dias | P1 |
| Migração LLM para Claude | Médio | 1-2 dias | P2 |
| Telefone default em prod | Baixo-médio | 0,25 dia | P2 |

---

## 7. Veredito das hipóteses

### H1 — Vitrine não converte: CONFIRMADA

- Não há captura de nome/email/telefone do visitante.
- Não há funil de conversão, evento de analytics ou tracking.
- CTAs levam para demo ou WhatsApp externo; quem termina a demo desaparece.
- Admin/leads é kanban interno da demo, sem export CSV.
- Evidência: `routes_chat.py:84` só recebe `niche`; `api.ts:52` só envia niche; nenhum formulário de captação.

### H2 — Vende 6 agentes, entrega 1: CONFIRMADA

- Catálogo tem 6 agentes em `agents.ts:23-88`.
- Runtime aceita apenas `niche` (não `agent_type`): `routes_chat.py:84-85`.
- ConversationProfile varia por `business_mode`, não por tipo de agente.
- Factory gera perfil por nicho comercial, não por agente.
- Apenas SDR tem demo executável; demais vão para "Pedir piloto": `AgentCard.tsx:54-63`.

### H3 — Não existe caminho de cliente real: CONFIRMADA

- Factory gera dados fictícios: `business_profile.py:13` — "fictitious company".
- Seeds são globais/hardcoded: `seeds/knowledge.py:22` — diretório único.
- KnowledgeChunk não tem `tenant_id`: `knowledge.py:25`.
- Retriever busca sem filtro de tenant: `retriever.py:46-94`.
- Não há onboarding, provisionamento, multi-tenancy ou WhatsApp Cloud API real.
- `contact_url` é global, não por tenant.

---

## 8. Commercial numbers — 2 erros corrigidos

| Erro | Onde | Era | Correto |
| --- | --- | --- | --- |
| Rate limit sessões/IP | STATUS_REPORT:200 | "50 sessões/IP/h" | "5 sessões/IP/h" |
| Total de testes | STATUS_REPORT:348 | "290+ testes" | "142 testes (115 backend + 7 frontend + 20 E2E)" |

Todos os outros números são rastreáveis (ver auditoria completa de `/commercial-numbers`).

---

## 9. Proposta de reordenação das fases

Com base na auditoria, a ordem original está correta com uma ressalva:

**Fase 1 (Vitrine vende)** continua prioritária. H1 confirmada significa que sem captura/funil, nenhuma visita gera lead.

Mas a decisão do Luiz de "validar primeiro com piloto real antes de implementar captura" modifica o escopo:

- Fase 1 reduzida: instrumentar funil server-side + CTA primário por rota (sem captura in-chat ainda). Captura real entra após feedback do primeiro piloto.
- Fase 2 (FAQ/RAG) segue como planejada.
- Fase 3 (Piloto → operação) segue como planejada.

**Recomendação:** não inverter fases. A ordem Vitrine → FAQ/RAG → Operação está correta. O que muda é o nível de captura na Fase 1: funil + analytics primeiro, formulário de lead depois do piloto.

---

## 10. Ações imediatas pós-auditoria

1. ~~Corrigir bug globstar no hook~~ ✅ (nesta sessão)
2. ~~Expandir protected-paths.txt~~ ✅ (nesta sessão)
3. ~~Corrigir 2 erros numéricos no STATUS_REPORT~~ ✅ (nesta sessão)
4. Iniciar Fase 1 quando pronto.
