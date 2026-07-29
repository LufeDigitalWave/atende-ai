---
name: audit-phase0
description: Auditoria completa do repositorio Atende AI antes de qualquer mudanca. Gera docs/AUDIT.md.
context: fork
agent: Explore
background: false
---

# Auditoria Fase 0 — Atende AI

Rodeiro de auditoria. Toda afirmacao cita arquivo e linha como evidencia.

## Roteiro

### 1. Matriz dos 6 agentes

Para cada agente do catalogo (SDR, Support, Appointment, FAQ/RAG, Civic, Collections):

- Status: `implementado` | `parcial` | `so marketing`
- Arquivo e linha que comprovam
- Se o card em `/agentes` existe sem Runtime correspondente, marcar como "marketing"

### 2. Fronteira demo x producao

Listar todos:

- `DEMO_MODE` ou equivalente
- Mocks e FakeProviders
- Dados ficticios hardcoded
- Fallbacks que vazariam para deploy de cliente

### 3. Generalizacao real

- O que Factory e Renderer abstraem de fato
- O que esta hardcoded para SDR
- Tamanho do gap para segundo agente funcional

### 4. Cobertura por risco

- Onde estao os testes
- O que NAO tem teste e causaria prejuizo em producao
- Guardrails sem teste dedicado

### 5. Preenchimento de protected-paths.txt

Verificar `.claude/protected-paths.txt` e adicionar caminhos faltantes:

- Modulo de rate limit
- Modulo de budget/token cap
- CSP e security headers
- Kill switch
- TTL de sessao
- CI workflow

### 6. Divida tecnica por risco comercial

Tabela: item, risco, custo estimado de correcao, prioridade.

### 7. Veredito de hipoteses

- **H1 — Vitrine nao converte:** evidencia de captura de lead, funil, evento de conversao.
- **H2 — Vende 6 agentes, entrega 1:** evidencia de Runtime para cada agente.
- **H3 — Nao existe caminho de cliente real:** evidencia de onboarding, tenant, base real.

### 8. Material comercial

Aplicar `/commercial-numbers` em `docs/commercial/`. Verificar que nomes de familia de LLM estao corretos.

## Entrega

Gerar `docs/AUDIT.md` com todas as secoes acima. Toda afirmacao tem evidencia (arquivo:linha).
