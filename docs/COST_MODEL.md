# Modelo de Custo — Atende AI

> Estimativa honesta de custo por conversa e por dia, com e sem prompt caching.
> Última atualização: 2026-07-13.

---

## Premissas

- Modelo padrão: **`claude-haiku-4-5`** (custo ~R$ 0,75 / 1M input tokens e R$ 3,75 / 1M output tokens, cotação 1 USD ≈ R$ 5).
- Prompt caching habilitado no system prompt + base RAG estática.
- Conversa típica: **8 turnos** do visitante + 8 respostas da Sofia.
- Janela de histórico: últimas 12 mensagens (ou 6 turnos).
- RAG top-3 chunks quando a mensagem parece pergunta (heurística simples).
- Extraction chamada **1 vez por turno** (tool use curto, separado do chat).
- Custo de embedding ignorado (rodamos `fake` por padrão na demo).

---

## Tokens por turno (chat + extraction)

### SEM prompt caching

| Componente | Tokens |
|---|---|
| System prompt (Sofia v1) | ~1.800 |
| Knowledge base injetada (top-3 chunks) | ~900 |
| Janela de histórico (12 mensagens) | ~2.400 |
| Mensagem atual do visitante | ~80 |
| Lead profile (resumo) | ~120 |
| **Input total** | **~5.300** |
| Resposta da Sofia (output) | ~150 |
| Extraction call (input) | ~600 |
| Extraction call (output, JSON) | ~80 |
| **Output total combinado** | **~230** |

### COM prompt caching

Como o system prompt + RAG são estáticos, a Anthropic cobra **10% do preço** de input em cache hits. Estimativa conservadora: **80% dos turnos** têm cache hit.

| Componente | Custo efetivo (após cache) |
|---|---|
| System prompt + RAG (cache hit 80%) | ~1.800 × 0.10 + 1.800 × 0.20 = 540 tokens |
| Histórico + lead profile + msg atual | ~2.600 |
| **Input médio efetivo** | **~3.140** |

---

## Custo por conversa (8 turnos)

### Sem cache
- Input: 5.300 × 8 = 42.400 tokens
- Output: 230 × 8 = 1.840 tokens
- **Custo: (42.400 × 0.75 + 1.840 × 3.75) / 1.000.000 ≈ R$ 0,039**

### Com cache (80% hit)
- Input: 3.140 × 8 = 25.120 tokens
- Output: 1.840 tokens
- **Custo: (25.120 × 0.75 + 1.840 × 3.75) / 1.000.000 ≈ R$ 0,026**

**Faixa honesta: R$ 0,02 a R$ 0,05 por conversa qualificada.**

---

## Custo diário

| Cenário | Conversas/dia | Custo/dia API | Infra (VPS) | **Total/mês** |
|---|---|---|---|---|
| Demo leve | 50 | ~R$ 1,3 | R$ 80 | ~R$ 120 |
| Demo média | 200 | ~R$ 5,2 | R$ 80 | ~R$ 235 |
| Demo pesada | 500 | ~R$ 13 | R$ 150 | ~R$ 540 |
| **Piloto cliente real** | 300 | ~R$ 7,8 | R$ 150 | ~R$ 385 |

**Defaults do MVP**: `DAILY_TOKEN_BUDGET=200000` (≈ R$ 5/dia em haiku com cache).

---

## Comparação com atendente humano

| Item | Atendente jr CLT | Agente IA |
|---|---|---|
| Salário + encargos | R$ 3.500 | — |
| Custo/mês (40h) | ~R$ 5.000 | — |
| Disponibilidade | 8h/dia, seg-sex | 24/7 |
| Conversas/dia | ~30 | ~500 (limite prático) |
| **Custo por conversa qualificada** | **R$ 11+** | **R$ 0,03** |

ROI claro: agente se paga com 10-15 conversas qualificadas/mês que ele teria perdido fora de horário.

---

## Quando o custo estoura

### Sinais de alerta
- Token count diário > 70% do budget → investigar.
- Conversas com > 30 turnos (cap não está fechando).
- Mesmo visitante mandando várias mensagens em loop (possível prompt injection).

### Mitigações
- Cap de sessão em código (não configurável).
- Rate limit 1 msg/2s.
- Banner "demo em alta demanda" quando budget estoura — não derruba o site.
- `usage_log` agrega por dia e por IP pra detectar abuso.

---

## Quando upgradar de modelo

| Modelo | Quando usar |
|---|---|
| **haiku 4.5** | Default demo, atendimento factual (RAG forte) |
| **sonnet 4.6** | Quando o lead faz perguntas complexas de planejamento, comparação de planos, ou negociação |
| **opus 4.8** | Em produção com base RAG fraca, ou quando o cliente quer "empatia premium" |

**Regra prática**: se a IA precisar só seguir roteiro e ler base → haiku. Se precisar raciocinar → sonnet. Opus raramente vale o custo (10x do sonnet).

---

## Auditoria

Todos os custos ficam em `usage_log` (Postgres). Admin mostra:
- Custo de hoje (R$)
- % do budget consumido
- Gráfico 14 dias
- Top 10 conversas mais caras

Em produção: webhook diário pra planilha Google Sheets do cliente.

---

## Honesto sobre o que NÃO entra no custo

- **Latência de rede** (proxy/Traefik): desprezível.
- **Postgres + pgvector em VPS pequeno**: R$ 50–100/mês.
- **Desenvolvimento / manutenção**: seu tempo, fora desse cálculo.
- **Re-embedding da base RAG** quando atualiza: ~R$ 0,01 por embedding (uma vez por arquivo).
- **Suporte humano do handoff** (vendedor real): é o "ROI humano" — não conta como custo da IA.