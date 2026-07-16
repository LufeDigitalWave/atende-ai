# ADR-001: Introdução do ConversationProfile

- **Status:** Aceito
- **Data:** 2026-07-16
- **Autor:** Luiz (Lufe Digital Wave)
- **Contexto:** Evolução v2 → v3 do Atende AI

---

## Contexto e problema

O v2 da arquitetura introduziu a separação dados-não-prompt com o
`BusinessProfile` — o LLM da factory gera JSON com dados de empresa, e um
template fixo renderiza esses dados em system prompt. Isso eliminou:

- Prompt injection via nicho.
- Inconsistência entre perfis (cada geração era diferente).
- Acoplamento entre regras de negócio e dados de empresa.

Porém, o **v2 ainda mantinha 5 campos de qualificação universais**
(`name`, `service_interest`, `complaint`, `budget_range`, `urgency`),
codificados no extractor heurístico e no scoring. Problema:

1. **Restaurante perguntando orçamento** é absurdo.
2. **B2B pulando budget como primeira pergunta** é alienante.
3. **Clínica sem `availability`** perde oportunidade de agendar rápido.
4. Cada nicho precisa de **campos, jornadas e regras DIFERENTES** —
   "qualificação" não é um tamanho único.

## Decisão

Introduzir o `ConversationProfile` como par obrigatório do
`BusinessProfile`, ambos empacotados em `NicheProfile`.

O `ConversationProfile` descreve **COMO** o agente deve se comportar, não
**O QUE** ele sabe. Inclui:

- `business_mode` — classificação do modelo de negócio
  (`reservation_based`, `appointment_based`, `consultative`,
  `transactional`, `mixed`).
- `primary_intents` — intenções comuns do nicho (3–8).
- `journeys` — fluxos conversacionais completos, cada um com:
  - intent, goal, qualification_fields, handoff_conditions,
    forbidden_questions.
- `qualification_fields` — campos coletáveis com regras:
  - `key`, `label`, `purpose`, `required_for`, `priority`,
    `ask_only_when_relevant`, `prohibited_before_intent`.
- `prohibited_behaviors` — o que NÃO fazer neste nicho.
- `handoff_rules` — condições pra passar pra humano.
- `lead_scoring_rules` — pontuação contextual por evento.
- `response_before_qualification` — flag de ouro: responder antes de
  qualificar.
- `max_questions_per_message` — 1 (padrão).

## Alternativas consideradas

### A. Múltiplos templates por nicho

Criar `agent_template_restaurante.md`, `agent_template_clinica.md`, etc.

- Prós: máxima customização.
- Contras: O(n) templates para manter; explosão de manutenção;
  difícil manter consistência de estilo; difícil testar genericamente;
  merge hell.

**Rejeitada:** escala O(n) é inviável com 5+ nichos.

### B. Prompt condicional no template

```
{% if business_mode == 'reservation_based' %}
  Não pergunte orçamento...
{% endif %}
```

- Prós: 1 template, mas com condicionais.
- Contras: Jinja no prompt = complexidade de debug; o template vira
  código; difícil auditar; LLM pode confundir com instrução.

**Rejeitada:** mix de dados com lógica é o que a v2 resolveu.

### C. ConversationProfile (escolhida)

- Template fixo, único, sem condicionais.
- Cada nicho gera dados DIFERENTES que são renderizados nas mesmas
  seções.
- Regras de comportamento ("não pergunte orçamento") são dados da
  `ConversationProfile`, renderizados na seção `PROHIBITED_BEHAVIORS`.

**Aceita:** mantém separação dados-não-prompt; escala O(1) em
templates; regras são auditáveis como dados.

## Consequências

### Positivas

1. **Cada nicho tem qualificação própria** sem mudar template.
2. **Restaurante nunca pergunta orçamento** porque não está nos
   `qualification_fields`.
3. **B2B pode ter `budget` como campo gradual** com
   `prohibited_before_intent=True`.
4. **Score é contextual** — usa os campos extraídos do perfil (não 5
   universais).
5. **Extractor é guiado** — recebe lista de `allowed_keys` do perfil.
6. **Testabilidade total** — Pydantic valida, testes checam render.

### Negativas

1. **Factory precisa gerar mais dados** (JSON mais complexo) → 1 retry
   + fallback.
2. **Frontend ainda usa legacy lead columns** (`name`, `service_interest`,
   etc.) → mapeamento `to_legacy_dict()` adicionado.
3. **Scoring v3 precisa de mapeamento campo→evento** — novo módulo
   `lead_scoring_v3.py`.
4. **Migration gradual** — v2 e v3 coexistem (prompt factory v2 e v3
   em paralelo).

### Riscos

- Factory gera `ConversationProfile` inválido → Pydantic captura +
  fallback estático (mitigado).
- LLM inventa `qualification_field.key` que extractor não mapeia →
  extractor filtra por `allowed_keys` (mitigado).
- Novo nicho com `business_mode` não suportado → fallback `mixed`
  (aceito).

## Medição de sucesso

- Zero ocorrências de "agente pergunta orçamento em restaurante" em
  30+ sessões de teste.
- Score de naturalidade (rubrica) ≥ 4.0 por turno.
- Zero placeholders `{...}` residuais no prompt renderizado.
- Testes ≥ 90% verdes no pipeline v3.

## Referências

- `backend/app/schemas/conversation_profile.py` — schema
- `backend/app/schemas/niche_profile.py` — container
- `backend/app/services/prompt_factory_v3.py` — geração
- `backend/app/services/prompt_renderer_v3.py` — render
- `backend/app/agent/prompts/agent_template_v3.md` — template
- `backend/app/agent/prompts/factory_v3.md` — meta-prompt
