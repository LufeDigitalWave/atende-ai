# ADR-003: Extração estruturada via LLM tool use

- **Status:** Aceito
- **Data:** 2026-07-16
- **Autor:** Luiz (Lufe Digital Wave)
- **Contexto:** Substituição do extractor heurístico por LLM na v3

---

## Contexto e problema

O extractor v2 era 100% heurístico: regex + keywords.

```python
# v2 (legacy)
if "meu nome é" in text: lead.name = ...
if any(w in text for w in ["melasma", "acne", ...]): lead.service_interest = ...
```

Problemas:

1. **Frágil a variações linguísticas.** "Me chamo Luiz" funciona,
   "Luiz aqui" não. "Quero tratar mancha no rosto" funciona,
   "quero acabar com essas manchas escuras" pode não.
2. **Extensão O(n).** Adicionar novo campo = novo bloco de regex +
   novos testes.
3. **Desacoplado do nicho.** O extractor não sabe quais campos são
   relevantes — extrai tudo que o regex pega, mesmo irrelevante.
4. **Não detecta intenção.** Não diferencia "quero reservar" de
   "quero ver o cardápio" — trata tudo como qualificação.
5. **Não detecta handoff.** Apenas 5 keywords fixas ("atendente",
   "humano", etc).

Com o `ConversationProfile` definindo campos dinâmicos por nicho,
o extractor heurístico não suporta a nova arquitetura.

## Decisão

Substituir o extractor por um **LLM via tool use** (OpenAI function
calling), com **fallback heurístico** pra degradação graciosa.

### Fluxo

```
mensagem do visitante + resposta do agente
  → build extraction prompt (system)
    - contexto: nicho, empresa, modo
    - intents possíveis (ConversationProfile.primary_intents)
    - campos permitidos (ConversationProfile.qualification_fields[].key)
    - handoff rules
    - lead summary atual (não sobrescrever)
  → LLM (gpt-4.1-mini, temperature=0.1, max_tokens=500)
    - tool: extract_lead_data()
    - tool_choice: forced
  → parse tool call arguments (JSON)
  → validar contra allowed_keys (Pydantic)
  → retornar ExtractedLeadData
```

### Schema da tool

```json
{
  "name": "extract_lead_data",
  "parameters": {
    "detected_intent": "string | null",
    "intent_confidence": "number (0-1)",
    "extracted_fields": [
      {"key": "string", "value": "any", "confidence": "number"}
    ],
    "should_handoff": "boolean",
    "handoff_reason": "string | null",
    "lead_stage_suggestion": "string | null",
    "notes": ["string"]
  }
}
```

### Validação pós-extração

1. **Filtro de keys:** campos com `key` fora do
   `ConversationProfile.qualification_fields` são descartados
   silenciosamente.
2. **Confidence threshold:** campos com `confidence < 0.3` podem ser
   descartados em regras futuras (atualmente aceitos).
3. **Não sobrescreve:** se o `existing_lead_summary` já tem um campo
   preenchido, o LLM é instruído a não retornar valor novo (a menos
   que tenha evidência explícita de correção).

### Fallback heurístico

Quando o LLM falha (timeout, rate limit, JSON inválido, API sem key):

```python
def _heuristic_fallback(user_message, agent_response, profile):
    # Regex conservadores:
    # - nome: "meu nome é X" / repetido pelo agente
    # - party_size: "N pessoas" / "somos N"
    # - date: "hoje" / "amanhã" / "sábado"
    # - time: "20h" / "20:00"
    # - handoff: 5 keywords
    # - intent: substring match nos primary_intents
```

O heurístico retorna `notes=["heuristic_fallback"]` para
rastreabilidade.

### Merge LLM + heurístico

No `routes_chat.py`, o heurístico roda DEPOIS do LLM e **adiciona
campos que o LLM perdeu** (mas não sobrescreve). Isso dá redundância:

```python
for hf in heuristic_result.extracted_fields:
    if hf.key not in existing_keys_from_llm:
        extraction.extracted_fields.append(hf)
```

## Alternativas consideradas

### A. Heurístico expandido (mais regex)

Adicionar regex para cada novo campo do ConversationProfile.

- Prós: sem custo extra de API; latência zero.
- Contras: manutenção O(n_campos × n_variações); frágil; não detecta
  intenção com nuance.

**Rejeitada:** não escala com campos dinâmicos por nicho.

### B. NER off-the-shelf (spaCy + custom)

Usar modelo de NER treinado pra português.

- Prós: sem custo de API por call; offline.
- Contras: precisa treinar com dados do domínio (não temos); não
  detecta intenção; latência de modelo on-premise; deployment
  complexo.

**Rejeitada:** overhead de treinamento sem dados.

### C. JSON mode (sem tool use)

Chamar LLM com `response_format={"type": "json_object"}` e schema
apenas no prompt.

- Prós: funciona em qualquer provider que suporte JSON mode.
- Contras: mais propenso a hallucination de keys; menos controle de
  schema; parsing menos confiável.

**Rejeitada parcialmente:** mantida como fallback se tool use falhar
(não implementado ainda).

### D. Tool use (escolhida)

- Prós: schema enforced pelo provider; parsing confiável;
  `tool_choice: forced` garante output; confidence por campo;
  latência aceitável (~300ms em gpt-4.1-mini).
- Contras: custo extra (1 call LLM por turno, ~600 tokens input +
  80 output); depende de provider com function calling.

**Aceita:** custo marginal (R$ 0,0004 por turno em gpt-4.1-mini)
e confiabilidade muito superior ao regex.

## Consequências

### Positivas

1. **Extração robusta** — entende variações linguísticas que regex
   nunca cobriria ("mesa pra 8 lá pro sábado, tamo em 20h" →
   party_size=8, date=sábado, time=20h).
2. **Detecção de intenção** — `detected_intent` com confidence
   permite routing de jornada.
3. **Handoff inteligente** — detecta pedidos implícitos ("prefiro
   falar com alguém de verdade") além dos 5 keywords.
4. **Campos dinâmicos** — qualquer `qualification_field.key` novo no
   perfil é automaticamente extraível sem código novo.
5. **Rastreabilidade** — `notes[]` registra observações internas.
6. **Graceful degradation** — se LLM falhar, heurístico ainda pega
   o básico (nome, números, keywords de handoff).

### Negativas

1. **Custo adicional** — +1 chamada LLM por turno (gpt-4.1-mini,
   ~600 tokens = ~R$ 0,0004/turno). Em 8 turnos = +R$ 0,003/conversa.
2. **Latência adicional** — ~300ms extra por turno (paralelo ao
   streaming, então não é perceptível ao visitante).
3. **Dependência de API** — offline precisa de fallback (implementado).
4. **Complexidade de merge** — LLM + heurístico podem conflitar
   (resolvido: LLM tem prioridade, heurístico só adiciona).

### Riscos mitigados

| Risco | Mitigação |
|---|---|
| LLM retorna key inválida | Filtro contra `allowed_keys` |
| LLM inventa valor | Prompt instrui "NUNCA invente" + confidence |
| LLM falha (timeout/rate) | Fallback heurístico + `notes=["heuristic_fallback"]` |
| JSON inválido no tool call | try/except → fallback |
| Custos explodem | gpt-4.1-mini (R$ 0,40/1M input); max_tokens=500 |

## Medição de sucesso

- Recall do extractor LLM ≥ 85% em dataset de cenários.
- Precision (campos corretos vs campos extraídos) ≥ 90%.
- Taxa de fallback para heurístico ≤ 15% das chamadas em produção.
- Latência P95 do extractor ≤ 500ms.
- Zero campos extraídos fora do `allowed_keys`.

## Referências

- `backend/app/services/lead_extractor.py`
- `backend/app/schemas/lead_extraction.py`
- `backend/app/tests/test_lead_extractor.py`
- `backend/app/tests/test_lead_extraction.py`
