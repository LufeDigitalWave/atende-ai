---
name: llmops
description: Convencoes de observabilidade, prompt management e evals para agentes de IA. Use ao instrumentar, versionar prompt ou criar eval.
---

# LLMOps — Convencoes Atende AI

## 6 Fases do Playbook

### 1. Audit

Antes de mudar prompt ou modelo:

- Documentar estado atual (versao, modelo, custo medio, qualidade percebida).
- Identificar o que medir antes de mexer.

### 2. Prompt Management

- Templates versionados em `backend/app/agent/prompts/`.
- Mudanca de template = bump de versao + entrada no changelog de `docs/AGENT_PROMPT.md`.
- Nunca editar prompt em producao sem versionar antes.
- Few-shot examples versionados junto ao template.

### 3. Observability (Langfuse)

- Toda chamada LLM deve ter trace no Langfuse (quando configurado).
- Trace inclui: session_id, modelo, tokens in/out/cached, latencia, custo.
- Se Langfuse estiver down: modo degradado (app nao cai, log warning).
- Pattern: `with langfuse.trace(name=...) as t:` no service layer.

### 4. Evals

- **Golden conversations:** dialogos de referencia com assercoes sobre:
  - Campos extraidos corretamente.
  - Transicoes de estado corretas.
  - Handoff acionado quando devido.
  - Preco/prazo/politica NUNCA inventado.
- **Eval de RAG:** perguntas respondiveis + adversariais (fora da base, ambiguas, premissa falsa).
- Evals rodam no CI como job dedicado.

### 5. Guardrails

- Testes dedicados em `tests/guardrails/`.
- Guardrail sem teste = "nao verificado".
- Guardrail desligado = teste vermelho.

### 6. CI/Lifecycle

- CI roda: lint, unit, integration, evals, guardrails, baseline check.
- Deploy so apos CI verde.
- Modelo novo: medição A/B antes de trocar (custo, qualidade, latencia).
- Trocar de modelo nao e decisao de codigo; e decisao de produto com dados.

## Padrao de tracing neste repo

```python
# Em services que chamam LLM:
from app.services.budget import log_usage

# Apos chamada:
log_usage(
    session_id=session_id,
    provider=provider_name,
    model=model_name,
    input_tokens=usage.input_tokens,
    output_tokens=usage.output_tokens,
    cached_tokens=usage.cached_tokens,
    cost_usd=calculated_cost,
)
```

Quando Langfuse estiver configurado, adicionar wrapper de trace.

## Regras para este repo

- Nao trocar modelo nesta rodada sem medicao antes/depois.
- Custo por conversa declarado em todo PR que afeta tokens.
- Prompt novo sem eval = nao mergeavel.
