# Agent Specification — Atende AI

**Versão:** 1.0  
**Data:** 2026-07-29  

## Conceito

Um agente é definido por **configuração**, não por código novo de Runtime. O Runtime seleciona pipeline baseado em `agent_type` persistido na sessão.

## Agent Types suportados

| agent_type | Template | Lead scoring | Extração | RAG | Handoff |
| --- | --- | --- | --- | --- | --- |
| `sdr` (default) | `agent_template_v3.md` | sim | sim (LLM + heuristic) | não (por enquanto) | sim (score/handoff rules) |
| `faq_rag` | `agent_template_faq_rag.md` | não | não | sim (retriever) | sim (regras no prompt) |

## Criação de sessão

```json
POST /api/sessions
{
  "niche": "clinica de estetica",
  "agent_type": "faq_rag"
}
```

- `agent_type` aceito: `sdr` ou `faq_rag`. Default: `sdr`.
- Persistido na tabela `sessions.agent_type`.
- Determina qual template de prompt é renderizado e quais pipelines rodam no loop.

## Pipeline por agent_type

### SDR (default)

```text
Factory → NicheProfile → Renderer (template v3) → LLM chat → Extração → Scoring → FSM → Handoff
```

### FAQ/RAG

```text
Factory → NicheProfile → Renderer (template FAQ/RAG) → RAG retrieval → LLM chat com contexto → Resposta direta
```

Diferenças:

- RAG retriever é chamado ANTES do LLM, com a mensagem do usuário como query.
- Top 5 chunks injetados no system prompt com instrução de responder apenas com base neles.
- Não roda lead extraction nem scoring (não é agente de vendas).
- Não roda FSM de qualificação.
- Handoff é por regra no prompt: "se não está na base, encaminhe para humano".

## Adicionando um novo agent_type

Para criar um terceiro agente (ex: `appointment`):

1. Adicionar ao enum/validation em `routes_chat.py:SessionCreateRequest`.
2. Criar template em `backend/app/agent/prompts/agent_template_<type>.md`.
3. Registrar o template path em `prompt_renderer_v3.py`.
4. Adicionar lógica condicional no loop SSE (`routes_chat.py:generate_sse`).
5. Criar golden conversations em `tests/golden/`.
6. Documentar aqui.

Nenhum campo novo precisa ser adicionado ao modelo `Session` (já tem `agent_type` varchar).

## Contrato do retriever

```python
class Retriever(ABC):
    async def retrieve(self, session: AsyncSession, query: str, top_k: int = 3) -> list[RetrievalResult]

class RetrievalResult:
    chunk_text: str
    source_file: str
    similarity: float
```

O retriever retorna chunks relevantes da `knowledge_chunks` table. Atualmente sem filtro por tenant (Fase 3 adicionará `tenant_id`).

## Regras de custo

- SDR: ~R$ 0,02-0,05/conversa (LLM chat + extração).
- FAQ/RAG: ~R$ 0,01-0,03/conversa (LLM chat sem extração, RAG é query local).
- Adicionar agent_type não muda custo significativamente; RAG é mais barato que SDR porque não roda extração.
