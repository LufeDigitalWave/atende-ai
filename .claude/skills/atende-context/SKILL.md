---
name: atende-context
description: Convencoes, arquitetura e invariantes do Atende AI. Use ao trabalhar em qualquer arquivo deste repositorio.
user-invocable: false
---

# Atende AI — Contexto do Projeto

## Arquitetura em 3 Layers

### Layer 1 — Factory (`backend/app/services/prompt_factory_v3.py`)

- Recebe nome de nicho (string, max 60 chars, sanitizado).
- Chama LLM (gpt-4.1-mini) para gerar `NicheProfile` = `BusinessProfile` + `ConversationProfile`.
- Cache TTL 1h por nicho normalizado.
- Gera dados FICTICIOS de demo. Nunca alimenta caminho de cliente real.
- Fallback estatico se LLM falhar (Sofia / Clinica Renova).

### Layer 2 — Renderer (`backend/app/services/prompt_renderer_v3.py`)

- Recebe `NicheProfile` + template fixo (`agent_template_v3.md`).
- Preenche placeholders deterministicamente. Sem chamada de LLM.
- Valida que nenhum placeholder residual ficou no output.
- Template versionado: mudanca = bump de versao + changelog.

### Layer 3 — Runtime (`backend/app/api/routes_chat.py` + services)

- Loop de conversa via SSE.
- RAG: retrieval por pgvector ou tsvector.
- Extracao: LLM tool_use + heuristic fallback.
- Scoring: contextual por nicho (campos do ConversationProfile).
- FSM: transicoes de estado (novo -> qualificando -> qualificado -> handoff).
- Handoff: deteccao por score >= 80, keywords ou regras do perfil.

## Guardrails e valores atuais

| Guardrail | Valor | Modulo |
| --- | --- | --- |
| Cap por sessao | 30 msgs | `routes_chat.py` |
| Rate limit msg | 2s | `services/rate_limit.py` |
| Rate limit sessoes | 50/IP/h | `services/rate_limit.py` |
| Budget diario | 200k tokens | `services/budget.py` |
| Input max | 500 chars | `schemas/chat.py` |
| Session TTL | 24h soft delete | `services/reset.py` |
| Kill switch | toggle admin | `services/killswitch.py` |

## Custo por conversa

R$ 0,02–0,05 (Haiku/gpt-4o-mini, 8 turnos medios, com prompt caching).
Toda mudanca que afete tokens, chamadas ou contexto declara o novo custo.

## Padrao de endpoint

Todo endpoint novo segue:

1. Rate limit (middleware ou decorator).
2. Validacao de input (Pydantic schema com limites).
3. Sanitizacao de PII em log (structlog pipeline filter).
4. Teste de autorizacao (admin = JWT Bearer; publico = rate limit reforçado).

## Regras inegociaveis

- Factory gera dado FICTICIO. Dado de cliente real nunca passa pela Factory.
- Numero de telefone real do Luiz NAO aparece no bundle de producao.
- URL de contato validada: apenas `wa.me` e `api.whatsapp.com` sobre HTTPS.
- Kill switch desligado = demo retorna 503, nao erro opaco.
- Guardrail desligado = teste vermelho no CI.
