---
name: guardrail-check
description: Verifica que todos os guardrails operacionais e headers de seguranca do Atende AI continuam ativos. Use antes de abrir PR e depois de qualquer mudanca em middleware, configuracao ou deploy.
allowed-tools: Bash(pytest *) Bash(curl *) Read Grep
---

# Guardrail Check — Atende AI

## O que fazer

1. Rodar `pytest tests/guardrails/ -v` (todos devem passar).
2. Conferir headers em producao via `curl -sI https://atendeai.lufedigitalwave.com.br/`.
3. Reportar tabela abaixo.

## Tabela de resultado

| Guardrail | Esperado | Observado | Veredito |
| --- | --- | --- | --- |
| Cap 30 msgs/sessao | msg 31 recusada | ? | ? |
| Rate limit 2s | 429 se imediata | ? | ? |
| Rate limit 50 sessoes/IP/h | sessao 51 recusada | ? | ? |
| Budget 200k tokens | novas conversas param | ? | ? |
| Input max 500 chars | 501 rejeitado | ? | ? |
| TTL 24h + soft delete | sessao expirada nao lida | ? | ? |
| Kill switch | demo retorna 503 | ? | ? |
| CSP header | presente com frame-ancestors | ? | ? |
| HSTS | max-age=31536000 | ? | ? |
| X-Frame-Options | SAMEORIGIN | ? | ? |
| X-Content-Type-Options | nosniff | ? | ? |
| PII em log | telefone/email/CPF nao aparece | ? | ? |
| Telefone real fora do bundle | grep no dist nao encontra | ? | ? |

## Regra critica

Um guardrail que NAO tem teste dedicado e reportado como "nao verificado", nunca como "ok".
Se algum guardrail falhar, NAO abra PR. Reporte e corrija primeiro.
