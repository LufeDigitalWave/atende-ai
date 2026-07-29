---
name: commercial-numbers
description: Regras para numeros em material comercial do Atende AI. Use ao editar qualquer arquivo em docs/commercial/.
paths: docs/commercial/**
user-invocable: false
---

# Commercial Numbers — Regras de Honestidade

## Principio

Todo numero em proposta, pitch, site ou material de venda precisa de origem rastreavel.

## Regras

1. **Origem obrigatoria:** cada numero cita de onde veio:
   - Arquivo de configuracao (ex: `config.py:daily_token_budget = 200_000`)
   - Query no banco (ex: `SELECT avg(tokens) FROM usage_log WHERE ...`)
   - Trace no Langfuse (ex: session cost p50)
   - Calculo explicito (ex: `500 conversas * R$ 0.04 = R$ 20`)

2. **Numero sem origem sai do material.** Nao se inventa numero "por estimativa" sem base.

3. **Capacidade so e descrita como existente se existe no Runtime.**
   - O catalogo lista 6 agentes, mas so o SDR tem Runtime funcional.
   - Material que descreve Support/Appointment/etc como "entregue" e falso.
   - Correto: "disponivel como configuracao" ou "no roadmap".

4. **Custo por conversa:** sempre citar modelo, numero medio de turnos e se tem caching.
   - Atual: R$ 0,02-0,05 com Haiku/gpt-4o-mini, 8 turnos, prompt caching.

5. **Margem:** calculada sobre custo real (LLM + infra), nao sobre custo teorico.

6. **Volume:** "30+ projetos" e validado pela lista de clientes na memoria.
   "70+ workflows n8n" vem da contagem real em producao dos clientes.

## Ao editar material comercial

- Verificar cada numero contra estas regras.
- Se um numero nao tem origem, marcar como `[VERIFICAR]` e reportar.
- Nunca publicar material com `[VERIFICAR]` nao resolvido.
