# Skill: Quality Assurance

Use esta skill quando o trabalho envolver:

- Rodar testes (`pytest`).
- Adicionar novos cenários de teste.
- Verificar regressões após mudança de prompt/factory/scoring.
- Avaliar naturalidade de conversas.
- Auditar score breakdown.
- Validar que o deploy tá saudável.

---

## Como rodar testes

```bash
cd backend
uv sync
pytest -v                              # todos
pytest tests/test_factory_v3.py -v     # factory v3
pytest tests/test_lead_extractor.py -v # extrator LLM
pytest tests/test_lead_scoring_v3.py -v # scoring v3
pytest tests/test_prompt_renderer_v3.py -v # renderer
pytest --cov=app                       # com cobertura
```

Testes NÃO tocam rede. Usam `FakeLLMProvider` + mocks + SQLite in-memory.

## Suíte existente

| Arquivo | Cobre |
|---|---|
| `test_factory_v2.py` | Factory v2 (legacy, manter compatível) |
| `test_factory_v3.py` | Factory v3 (sanitização, fallback, cache, NicheProfile) |
| `test_conversation_profile.py` | Schema ConversationProfile (validação Pydantic) |
| `test_prompt_renderer_v3.py` | Render template sem placeholders residuais |
| `test_lead_extractor.py` | Extractor LLM (mock) + heuristic fallback |
| `test_lead_extraction.py` | Schema ExtractedLeadData (validação Pydantic) |
| `test_lead_scoring_v3.py` | Scoring contextual (por nicho, cumulativo, cap) |
| `test_extractor.py` | Extractor heurístico legacy |
| `test_scoring.py` | Scoring legacy 5-field |
| `test_states.py` | FSM (transições permitidas/proibidas) |
| `test_integration.py` | Fluxo ponta-a-ponta fake |
| `test_guards.py` | Rate limit, cap, budget |

## Checklist pré-release

- [ ] `pytest -v` tudo verde (0 failures, 0 errors).
- [ ] Cobertura ≥ 60% em `app/agent/`, `app/services/`.
- [ ] Cada nicho testado (restaurante, clínica, B2B) tem ≥1 fixture.
- [ ] Fallback profile (Sofia) renderiza sem erro.
- [ ] Template v3 não tem placeholders residuais.
- [ ] Scoring v3 com extração completa = score esperado.
- [ ] Handoff detectado em keywords de handoff (5+).
- [ ] Extractor filtra keys não-autorizadas.

## Como adicionar cenário de teste

### 1. Teste de extração (novo nicho)

```python
# tests/test_lead_extractor.py
def _pet_shop_profile() -> NicheProfile:
    business = BusinessProfile(...)
    conversation = ConversationProfile(
        business_mode="mixed",
        primary_intents=["consulta", "banho", "vacina", "compra"],
        qualification_fields=[
            QualificationField(key="pet_name", label="Nome do pet", purpose="Identificar"),
            QualificationField(key="pet_type", label="Tipo", purpose="Serviço adequado"),
            QualificationField(key="service", label="Serviço", purpose="Direcionar"),
        ],
        ...
    )
    return NicheProfile(business=business, conversation=conversation)

def test_pet_name_extraction():
    result = _heuristic_fallback("Meu cachorro se chama Rex", "...", _pet_shop_profile())
    # Assert...
```

### 2. Teste de scoring (novo perfil)

```python
# tests/test_lead_scoring_v3.py
def test_pet_shop_scoring():
    profile = _pet_shop_profile()
    ext = ExtractedLeadData(
        detected_intent="banho",
        extracted_fields=[
            ExtractedField(key="pet_name", value="Rex", confidence=0.9),
            ExtractedField(key="service", value="banho e tosa", confidence=0.9),
        ],
    )
    score, breakdown = compute_score_v3(ext, profile)
    assert score > 0
    assert "intent_banho" in breakdown
```

### 3. Teste de render (template completo)

```python
# tests/test_prompt_renderer_v3.py
def test_new_niche_renders():
    prompt = render_prompt(_pet_shop_profile())
    assert "Rex" not in prompt  # dados de teste não contaminam
    assert "banho" in prompt or "pet" in prompt
    # Sem placeholder residual
    import re
    assert re.findall(r"\{[a-z_]+\}", prompt) == []
```

## Avaliação manual (rubrica)

Quando teste automatizado não é suficiente (naturalidade, tom), usar
a rubrica de 5 dimensões do `docs/EVALUATION.md` seção 3:

1. Naturalidade linguística (1-5)
2. Aderência à intenção (1-5)
3. Respeito à quantidade de perguntas (1-5)
4. Economia conversacional (1-5)
5. Conformidade com prohibited_behaviors (1-5)

Nota mínima aceitável: 4.0/turno, 4.3 média geral.

## Monitoramento em produção

| Sinal | Onde olhar | Ação |
|---|---|---|
| Score=0 em lead com campos | `score_breakdown` no admin | Bug no mapeamento campo→evento |
| State travado em `em_qualificacao` | Admin → Leads | Bug no FSM ou extractor |
| Handoff não disparou | `timeline_events` | Verificar handoff_rules + extractor |
| Custo anormal | Admin → Custos | Verificar `usage_log` GROUP BY IP |
| Extractor sempre em fallback | Logs (`heuristic_fallback`) | API key expirada ou rate limit |

## Debugging rápido

```bash
# Testar extração isolada
cd backend
uv run python -c "
import asyncio
from app.services.lead_extractor import _heuristic_fallback
from app.services.prompt_factory_v3 import FALLBACK_PROFILE

result = _heuristic_fallback(
    'Quero reservar para 4 pessoas amanhã às 19h',
    'Ótimo!',
    FALLBACK_PROFILE
)
print([f'{f.key}={f.value}' for f in result.extracted_fields])
"

# Testar scoring isolado
uv run python -c "
from app.schemas.lead_extraction import ExtractedLeadData, ExtractedField
from app.services.lead_scoring_v3 import compute_score_v3
from app.services.prompt_factory_v3 import FALLBACK_PROFILE

ext = ExtractedLeadData(
    detected_intent='avaliacao',
    extracted_fields=[
        ExtractedField(key='customer_name', value='Maria', confidence=0.9),
        ExtractedField(key='need', value='melasma', confidence=0.9),
    ]
)
score, breakdown = compute_score_v3(ext, FALLBACK_PROFILE)
print(f'score={score}, breakdown={breakdown}')
"
```

## Referências

- Cenários completos: `docs/EVALUATION.md` seção 2
- Rubrica: `docs/EVALUATION.md` seção 3
- Critérios de qualidade: `docs/EVALUATION.md` seção 4
- Processo A/B: `docs/EVALUATION.md` seção 5
