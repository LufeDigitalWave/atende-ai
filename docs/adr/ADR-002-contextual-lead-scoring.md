# ADR-002: Scoring contextual por intenção

- **Status:** Aceito
- **Data:** 2026-07-16
- **Autor:** Luiz (Lufe Digital Wave)
- **Contexto:** Evolução v2 → v3 do scoring de leads

---

## Contexto e problema

O scoring v2 era determinístico e universal:

```python
# v2 (legacy)
name_filled        → +20
service_interest   → +20
complaint_filled   → +15
budget_range_set   → +20
  budget_mid/high  → +10
urgency_set        → +15
  urgency_alta     → +10
```

Problemas:

1. **Restaurante:** lead que informa nome + 8 pessoas + data + horário
   (campos que realmente importam) score apenas 20 (nome). Os campos
   relevantes (`party_size`, `reservation_date`, `reservation_time`) não
   existem no schema legacy.
2. **Clínica:** `complaint` dá +15 mas `availability` (mais relevante pra
   agendamento) não pontua.
3. **B2B:** `budget_range` dá +30 combinado (mais que qualquer outro), mas
   em consultiva orçamento é informação tardia — distorce o score.
4. **O score ≥ 80 disparava "qualificado"** no FSM, mas com pesos
   universais era possível atingir 80 sem ter informação útil pro nicho.

## Decisão

Implementar `lead_scoring_v3.py` com scoring contextual:

1. Score é calculado contra o `ConversationProfile.lead_scoring_rules` do
   nicho.
2. Cada campo extraído é mapeado para um **evento de scoring** (ex:
   `customer_name` → `name_informed`, `party_size` → `party_size_informed`).
3. Pontos vêm do perfil (`lead_scoring_rules: {"name_informed": 10,
   "party_size_informed": 15, ...}`) ou de defaults quando o perfil não
   define.
4. Score é **cumulativo** (soma extração atual com extração de turnos
   anteriores via `_build_cumulative_extraction`).
5. Cap em 100.
6. Handoff é tratado pela FSM, não pelo score (score não soma ponto de
   handoff).

### Exemplo concreto: restaurante

```
Extração: intent=reserva, name=Luiz, party_size=8, date=sábado, time=20h
Scoring:
  intent_reserva      → 10
  name_informed       → 10
  party_size_informed → 15
  date_informed       → 15
  time_informed       → 15
  TOTAL              = 65
```

Compare com v2: o mesmo lead pontuaria **20** (apenas `name_filled`).

### Exemplo concreto: B2B

```
Extração: intent=problema, problem_type=churn, urgency=alta, decision_maker=sim
Scoring:
  intent_problema         → 10
  problem_informed        → 15
  urgency_informed        → 15
  decision_maker_informed → 20
  TOTAL                  = 60
```

Note: orçamento **não** está presente e lead já é qualificável pra handoff.

## Alternativas consideradas

### A. Pesos universais com faixa por nicho

Manter os 5 campos mas ajustar os pesos (ex: `budget_range_set=0` em
restaurante).

- Prós: menos código novo.
- Contras: continua com 5 campos fixos; novas jornadas não cabem;
  campos novos (`party_size`) não têm coluna.

**Rejeitada:** paliativo que não resolve.

### B. Score ML (regressão/classificação)

Treinar modelo com conversas reais → score predictivo.

- Prós: adaptativo.
- Contras: precisa de dados que não existem (demo nova, zero histórico);
  caixa-preta (não explicável); muito overhead pro MVP.

**Rejeitada:** impraticável pra demo/MVP sem dados.

### C. Scoring contextual determinístico (escolhida)

- Prós: explicável, auditável, configurável por nicho, testável.
- Contras: precisa de mapeamento campo→evento (manutenção manual).

**Aceita:** melhor trade-off para MVP. Score explicável = argumento de
venda no demo.

## Implementação

### Módulos

- `backend/app/services/lead_scoring_v3.py` — `compute_score_v3(extraction,
  profile) → (score, breakdown)`.
- `backend/app/api/routes_chat.py` — chama scoring v3 com extração
  cumulativa.
- `backend/app/services/lead_scoring_v3.py:compute_score_legacy()` —
  preservado como fallback.

### Mapeamento campo→evento

```python
mapping = {
    "customer_name": "name_informed",
    "party_size": "party_size_informed",
    "reservation_date": "date_informed",
    "reservation_time": "time_informed",
    "need": "need_informed",
    "urgency": "urgency_informed",
    "availability": "availability_informed",
    "problem_type": "problem_informed",
    "decision_maker": "decision_maker_informed",
    "product_interest": "product_informed",
    "delivery_zone": "delivery_zone_informed",
    "payment_preference": "payment_informed",
}
```

Novos campos são adicionados aqui quando o `ConversationProfile` introduz
nova `qualification_field.key`.

### Cumulatividade

O scoring não roda só na extração do turno atual. A cada turno, o
`routes_chat.py` reconstrói uma `ExtractedLeadData` cumulativa:

```python
cumulative = _build_cumulative_extraction(lead, current_extraction, profile)
score, breakdown = compute_score_v3(cumulative, profile)
```

Isso garante que um lead que deu nome no turno 2 e data no turno 4 tenha
score=2 somando ambos, não score=1 ignorando o turno 2.

## Consequências

### Positivas

1. Score reflete qualificação REAL do nicho.
2. `score_breakdown` é legível pelo admin (e aparece no CRM).
3. Restaurante chega a score 65 com reserva completa (vs 20 no v2).
4. B2B pode ter score 60 sem orçamento (viável pra handoff).
5. Score é argumento comercial ("veja, o lead está em 65 porque tem
   nome, grupo, data e hora — falta só confirmar").

### Negativas

1. Mapeamento campo→evento precisa crescer com novos nichos.
2. Defaults (10 pontos) para campo desconhecido são genéricos.
3. Lead legacy (sem ConversationProfile) precisa de fallback legacy
   scoring.

### Migração

- v2 scoring (`compute_score`) permanece em `agent/scoring.py` (FSM usa).
- v3 scoring vive em `services/lead_scoring_v3.py`.
- `routes_chat.py` usa v3 quando `niche_profile` disponível.
- Frontend consome SSE `score_update` indiferente à versão.

## Medição de sucesso

- Correlação score≥50 com handoff produtivo ≥ 70%.
- Zero leads com score=0 que deveriam ter campos preenchidos.
- `score_breakdown` sempre explicando ≥80% do total.
- 10+ testes em `test_lead_scoring_v3.py` cobrindo 3 nichos.

## Referências

- `backend/app/services/lead_scoring_v3.py`
- `backend/app/api/routes_chat.py:_build_cumulative_extraction()`
- `backend/app/tests/test_lead_scoring_v3.py`
