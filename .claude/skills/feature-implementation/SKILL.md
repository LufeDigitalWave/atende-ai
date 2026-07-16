# Skill: Feature Implementation

Use esta skill quando o trabalho envolver:

- Adicionar novo nicho de negócio.
- Estender `ConversationProfile` (novos campos, novas jornadas).
- Implementar novo handler de state/transição.
- Mudar modelo de scoring.
- Integrar novo provider LLM.
- Expandir extractor (novos campos, nova heurística).

---

## Arquitetura v3 em camadas

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: FACTORY (dados por nicho)                          │
│ factory_v3.md (meta-prompt) → gpt-4.1-mini → JSON          │
│ BusinessProfile + ConversationProfile (validated)            │
│ NicheProfile (package) + cache 1h                           │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: RENDERER (template fixo versionado)                │
│ agent_template_v3.md + NicheProfile data                    │
│ → deterministic system prompt                               │
│ → renderizado pra LLM do agente                             │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: RUNTIME (agente + extrator + scoring + state)      │
│ loop.py: retrieve (RAG) → chat → extract → score → state    │
│ lead_extractor.py: LLM tool use + heuristic fallback       │
│ lead_scoring_v3.py: contextual por nicho                    │
│ states.py: FSM transitions                                  │
└─────────────────────────────────────────────────────────────┘
```

**Implicação:** mudança em layer 1 (Factory) ou layer 2 (Renderer)
Requer apenas alteração de dados/template, não código. Novos nichos
escalam O(1) em linhas de código.

## Checklist: adicionar novo nicho

### 1. Entender o domínio

- [ ] Qual o `business_mode`? (reservation_based, appointment_based, etc)
- [ ] Quais as intenções principais? (3-6)
- [ ] Quais os campos que realmente importam pro agendamento?
- [ ] Qual é a objeção mais comum?
- [ ] Orçamento é pergunta legítima?
- [ ] Qual a sequência natural de perguntas?

### 2. Atualizar factory_v3.md (se necessário)

- [ ] Adicionar novo `business_mode` à lista de exemplos?
- [ ] Exemplificar boas práticas pra esse modo?
- [ ] Documentar campos que o Factory deve gerar?

### 3. Criar ConversationProfile

```python
conversation = ConversationProfile(
    business_mode="...",
    primary_intents=["int1", "int2", ...],
    journeys=[
        ConversationJourney(
            intent="int1",
            description="...",
            response_goal="...",
            suggested_cta="...",
            qualification_fields=[...],
            handoff_conditions=[...],
            forbidden_questions=[...],
        ),
    ],
    qualification_fields=[
        QualificationField(
            key="field_key",
            label="Label legível",
            purpose="Por que coletar",
            required_for=["intent1"],
            priority="high|medium|low",
            ask_only_when_relevant=True,
            prohibited_before_intent=False,
        ),
    ],
    prohibited_behaviors=["Não fazer X", ...],
    handoff_rules=["Condição 1", ...],
    lead_scoring_rules={
        "event1": 10,
        "event2": 15,
        "event3": 20,
    },
    proactive_opening_strategy="Como abrir...sem 'como posso ajudar?'",
    response_before_qualification=True,
    max_questions_per_message=1,
)
```

Campos críticos:

- `business_mode` — determina defaults de qualificação.
- `prohibited_behaviors` — impede erros típicos (ex: orçamento em
  restaurante).
- `lead_scoring_rules` — **ninguém** nasce com pesos genéricos.
  Estudar o nicho antes.
- `response_before_qualification` — quase sempre `True`.

### 4. Criar fallback estático (para quando factory falha)

Em `prompt_factory_v3.py:_fallback_business()` e
`_fallback_conversation()`:

```python
def _fallback_conversation_pet_shop() -> ConversationProfile:
    return ConversationProfile(
        business_mode="mixed",
        primary_intents=["consulta", "banho", "vacina", "compra"],
        journeys=[
            ConversationJourney(
                intent="banho",
                description="Cliente quer banho/tosa",
                response_goal="Agendar banho com horário e pet info",
                suggested_cta="Posso agendar um banho pra você.",
                qualification_fields=["pet_name", "pet_type", "availability"],
                handoff_conditions=["horário + pet info confirmados"],
                forbidden_questions=[],
            ),
        ],
        qualification_fields=[
            QualificationField(key="pet_name", label="Nome do pet", purpose="Personalizar"),
            QualificationField(key="pet_type", label="Tipo", purpose="Serviço adequado"),
            QualificationField(key="availability", label="Dia/horário", purpose="Agendar"),
        ],
        prohibited_behaviors=[
            "Não prometer que o pet fica super fofo",
            "Não usar nomes de outras clínicas",
        ],
        handoff_rules=["Agendamento completo", "Cliente pede humano"],
        lead_scoring_rules={
            "intent_detected": 10,
            "pet_type_informed": 15,
            "availability_informed": 25,
        },
        proactive_opening_strategy="Apresentar serviços e oferecer agendamento",
    )
```

### 5. Adicionar testes

```bash
# tests/test_lead_extractor.py — nova fixture
def _pet_shop_profile() -> NicheProfile:
    # ... (usar fallback + business acima)

def test_pet_shop_name_extraction():
    result = _heuristic_fallback(...)
    # assert...

def test_pet_shop_handoff_complete():
    # ...

# tests/test_prompt_renderer_v3.py — novo test
def test_pet_shop_renders_without_placeholder():
    prompt = render_prompt(_pet_shop_profile())
    import re
    assert re.findall(r"\{[a-z_]+\}", prompt) == []

# tests/test_lead_scoring_v3.py — novo test
def test_pet_shop_scoring():
    # ...
```

### 6. Atualizar documentação

- [ ] Adicionar 5+ cenários em `docs/EVALUATION.md` seção 2.
- [ ] Adicionar exemplo em `docs/CONVERSATION_DESIGN.md`.
- [ ] Atualizar changelog em `docs/AGENT_PROMPT.md`.
- [ ] Update `CLAUDE.md` se o novo nicho muda alguma regra.

### 7. Testar

```bash
pytest tests/test_lead_extractor.py tests/test_prompt_renderer_v3.py tests/test_lead_scoring_v3.py -v
cd backend
LLM_PROVIDER=fake uv run python
# Manual: rodar 5 conversas fake pelo admin
```

---

## Checklist: expandir extraction

Quando precisar extrair novo campo (ex: `pet_breed`):

1. Adicionar ao `ConversationProfile.qualification_fields` (novo nicho).
2. Atualizar `_field_to_scoring_event()` em `lead_scoring_v3.py`:
   ```python
   "pet_breed": "breed_informed",
   ```
3. Adicionar ao mapeamento heurístico em `lead_extractor.py._heuristic_fallback()`
   se for detectável:
   ```python
   # Heuristic para raça
   breed_keywords = ["poodle", "golden", "labrador", ...]
   ```
4. Teste: `test_lead_extractor.py` nova fixture.

---

## Checklist: mudar scoring rules

Antes de mudar `ConversationProfile.lead_scoring_rules`:

1. Analisar dados históricos (se houver).
   - Qual campo correlaciona mais com conversão?
   - Qual com handoff produtivo?
2. A/B test a mudança (7 dias, significância p < 0,05).
3. Documentar rationale no changelog.
4. Testar que score ≥ 50 mantém correlação com handoff.

---

## Checklist: integrar novo LLM provider

Para adicionar novo provider (ex: Gemini, Cohere):

1. Criar classe em `services/llm.py`:
   ```python
   class GeminiProvider(LLMProvider):
       async def chat_stream(...):
           # Implementation
   ```
2. Registrar em `get_llm_provider()` factory.
3. Adicionar env vars em `core/config.py`.
4. Adicionar a `.env.example`.
5. Testar com `FakeLLMProvider` first (zero deps).
6. Testes: mock do novo provider em `tests/`.

---

## Pipeline de mudança

```
Plano escrito (GitHub issue + ADR)
  ↓
Implementação (branch, código)
  ↓
Pytest local (pytest -v)
  ↓
Comit + push (conventional commits)
  ↓
Code review (checklist de features)
  ↓
Merge pra main
  ↓
Deploy dev (docker-compose up em VPS)
  ↓
QA manual (5+ cenários por nicho)
  ↓
Merge pra prod
  ↓
Monitor (logs, score_breakdown, custo)
```

---

## Referências rápidas

- Arquitetura: `CLAUDE.md` (seção Arquitetura)
- Conversation design: `docs/CONVERSATION_DESIGN.md`
- Avaliação: `docs/EVALUATION.md`
- Scoring: `docs/adr/ADR-002-contextual-lead-scoring.md`
- Extração: `docs/adr/ADR-003-structured-lead-extraction.md`
