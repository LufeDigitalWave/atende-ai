# Anatomia do Prompt — Sofia v2 (Factory v2 Data-Not-Prompt)

> **v2.0 (2026-07-15):** Complete rewrite. LLM generates DATA (BusinessProfile JSON), not instructions.
> Template is fixed, versionado, e contém as regras de batalha.

---

## Arquitetura — o que mudou

### v1 (old — deprecated)
```
nicho → LLM writes entire system_prompt as free text → chatbot uses it
                         ❌ inconsistent, vulnerable to injection
```

### v2 (now — factory-v2 branch)
```
nicho → [meta-prompt → gpt-4.1-mini → BusinessProfile JSON]
     → Pydantic validation
     → render agent_template_v2.md with the profile
     → final system prompt (cached 1h)
                         ✅ consistent, injection-safe, auditable
```

---

## Componentes

### 1. Meta-Prompt (`backend/app/agent/prompts/factory_v2.md`)

Templa que instrui o LLM (gpt-4.1-mini) a gerar um JSON estruturado:

```json
{
  "agent_name": "Sofia",
  "company_name": "Clínica Renova",
  "city": "São Paulo",
  "tagline": "Estética avançada",
  "services": [
    {
      "name": "Limpeza profunda",
      "price_installments": "12x R$ 89",
      "price_cash": "R$ 1.068",
      "duration_or_scope": "60 min",
      "highlight": false
    }
  ],
  "qualification_extra_question": "Qual região do corpo?",
  "faq": [{"q": "...", "a": "..."}],
  "common_objections": [{"objection": "...", "guideline": "..."}],
  "tone_notes": "calorosa, profissional",
  "opening_message": "Oi! Sou a Sofia...",
  "suggestions": ["...", "...", "..."]
}
```

### 2. BusinessProfile Schema (`backend/app/schemas/business_profile.py`)

Pydantic model que valida o JSON:
- agent_name: brasileiro, 2-30 chars
- company_name: fictício, 3-60 chars
- services: 3-5 items com preços em formato específico (`Nx R$ X`)
- faq: exatamente 5 items
- common_objections: exatamente 3 items
- Validações: regex pra preços, comprimento mínimo/máximo

### 3. Agent Template (`backend/app/agent/prompts/agent_template_v2.md`)

**Este arquivo é a alma do produto.** Contém as regras invioláveis do agente:
- Uma pergunta por vez
- Extração oportunística de 5 campos
- Formato de preço obrigatório
- Nunca desconto, nunca resultado clínico
- Handoff quando qualificado
- Anti-alucinação
- Redirecionamento de fora-de-escopo

Variáveis renderizadas do profile:
- `{agent_name}`, `{company_name}`, `{city}`, `{tagline}`
- `{qualification_extra_question}`
- `{services_rendered}` (lista formatada com preços)
- `{faq_rendered}`
- `{objections_rendered}`
- `{tone_notes}`

### 4. Factory Service (`backend/app/services/prompt_factory.py`)

```python
async def generate_niche_prompt(niche: str) -> CachedProfile:
    # 1. Sanitize niche (max 60 chars, no line breaks) → injection prevention
    # 2. Check cache (TTL 1h)
    # 3. Call gpt-4.1-mini with meta-prompt
    # 4. Parse JSON, validate with BusinessProfile
    # 5. If invalid → retry once → fallback to static profile (Sofia/Clínica Renova)
    # 6. Render template with profile
    # 7. Cache (1h), return CachedProfile(profile, system_prompt)
```

Functions:
- `sanitize_niche(niche: str) -> str` — removes injection vectors
- `render_template(profile: BusinessProfile) -> str` — fills template vars
- `generate_niche_prompt(niche: str)` — full pipeline
- `get_cached_prompt(niche: str)` — cache lookup
- `clear_cache()` — used by reset job

### 5. Niche Selector (`frontend/src/components/NicheSelector.tsx`)

8 predefined niches + custom input:
```tsx
const NICHES = [
  { id: 'clinica_estetica', label: 'Clínica de Estética', emoji: '💆' },
  { id: 'pet_shop', label: 'Pet Shop / Veterinária', emoji: '🐾' },
  // ...
];
```

On select → `createSession(niche)` → POST `/api/sessions` with `{niche: "..."}`

### 6. Routes (`backend/app/api/routes_chat.py`)

```python
POST /api/sessions {niche: "clínica de estética"}
# Calls generate_niche_prompt(niche) → returns agent_name, company_name, suggestions

POST /api/sessions/{id}/messages
# SSE generator loads cached system prompt and streams agent response
```

---

## Vantagens da arquitetura v2

| Aspecto | v1 | v2 |
|---|---|---|
| **Consistência** | LLM gera prompt inteiro → variável | Template fixo → consistent |
| **Injeção** | `{niche}` entra no system prompt | `niche` só gera DADOS, template é imune |
| **Auditabilidade** | Prompt muda a cada LLM call | Template versionado (`agent_template_v2.md`) + changelog |
| **Manutenção** | Melhorar regras = reescrever todos os prompts gerados | Melhorar regras = editar 1 template + bump versão |
| **Testabilidade** | Hard to test (free-form text) | Schema validation + template rendering tests |
| **Cost** | Full system prompt on every call | Profile cache hit = reuse same cached system prompt |

---

## Como testar a factory v2

### Teste manual (dev)

```bash
cd backend
uv run python

from app.services.prompt_factory import generate_niche_prompt, render_template
import asyncio

async def test():
    cached = await generate_niche_prompt("consultório odontológico")
    print(cached.profile.agent_name)  # e.g., "Dra. Ana"
    print(cached.profile.company_name)  # e.g., "Sorriso Perfeito"
    print(cached.system_prompt[:200])  # Template rendered

asyncio.run(test())
```

### Teste automatizado

```bash
cd backend
pytest tests/test_factory_v2.py -v
```

8+ testes covering:
- Sanitização (injection prevention)
- Schema validation (BusinessProfile)
- Template rendering (no vars remain)
- Cache (TTL, isolation)
- Fallback (on LLM failure, no API key)

### Teste de regressão (before releasing)

Run demo com 5 nichos diferentes (predefined + 1 custom):
- Verify agent has correct name, company, services
- Verify chat flows naturally (extração, score)
- Verify admin dashboard updates lead state
- Verify cost tracking works (tokens counted)

---

## Changelog

### v2.0 (2026-07-15)
- Complete rewrite: LLM generates BusinessProfile JSON (data), not system prompt
- Template is fixed and versionado (`agent_template_v2.md`)
- Schema validation with Pydantic (BusinessProfile)
- Injection-safe niche sanitization (max 60 chars, no line breaks)
- Cache with 1h TTL per niche
- Fallback to static profile (Sofia/Clínica Renova) on LLM failure
- 8+ tests for factory pipeline
- Factory model: gpt-4.1-mini (not 4o-mini)
- Agent chat model: claude-haiku-4-5 (with prompt caching on system prompt)

### v1 (2026-07-13) — deprecated
- LLM generated entire system prompt as free text
- No schema validation
- Vulnerable to prompt injection via niche input
- Template-based rendering (old agent_template_v1.md)
- Sofia hardcoded for "clinica de estetica" niche

---

## Próximas melhorias (pós-MVP)

1. Multi-language factory (gere profiles em FR/EN/ES, agente responde no idioma)
2. A/B test factory versions (v2a vs v2b com diferentes meta-prompts)
3. RAG-driven factory (gere profile consultando web para dados do ramo)
4. Admin UI pra editar profiles sem regenerating (override factory output)
5. Metrics dashboard (qual factory version tem melhor lead quality?)
