---
name: ship-phase
description: Fecha uma fase do roadmap do Atende AI - roda a suite completa, verifica guardrails, escreve o relatorio e abre o PR.
argument-hint: [numero-da-fase]
allowed-tools: Bash(git *) Bash(gh pr *) Bash(pytest *) Bash(npm *) Bash(npx playwright *)
---

# Ship Phase — Ritual de Fechamento

## Sequencia obrigatoria

1. **Suite backend:** `cd backend && pytest -v --tb=short`
2. **Unit frontend:** `cd frontend && npm test`
3. **E2E frontend:** `cd frontend && npm run test:e2e`
4. **Guardrail check:** invocar `/guardrail-check`
5. **Security review:** invocar `/security-review` no diff da fase
6. **Diff de caminhos protegidos:** `git diff HEAD -- .claude/ tests/guardrails/` deve ser VAZIO
7. **Relatorio de fase:** escrever em `docs/phases/phase-<N>-report.md`
8. **PR em ingles:** titulo curto, body com impacto declarado em custo por conversa

## Regras

- Se QUALQUER etapa falhar, NAO abre PR. Reporta e corrige.
- O relatorio inclui: o que mudou, o que quebrou, o que ficou pendente, qual decisao depende do Luiz, recomendacao para a fase seguinte.
- PR body declara custo por conversa antes e depois da mudanca.
- Se o custo mudou, explicar por que e se a margem dos pacotes ainda fecha.

## Formato do relatorio

```markdown
# Phase <N> Report

## Summary
...

## Changes
| File | Type | Description |
| --- | --- | --- |

## Test results
| Suite | Result |
| --- | --- |

## Guardrail check
(tabela do /guardrail-check)

## Cost impact
- Before: R$ X.XX/conversa
- After: R$ X.XX/conversa
- Reason: ...

## Pending
...

## Recommendation for next phase
...
```
