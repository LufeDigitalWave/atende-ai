# Onboarding Runbook — Atende AI

**De "contrato assinado" a "agente no ar"**

## Meta de tempo

| Pacote | Meta total | Responsável |
| --- | --- | --- |
| Starter | ≤ 3 dias úteis | Luiz |
| Pro | ≤ 7 dias úteis | Luiz |
| Business | ≤ 15 dias úteis | Luiz + sócio |

## Etapas

### 1. Receber documentos do cliente (Dia 0)

**Tempo:** 30 min  
**Responsável:** Sócio comercial  
**Entregável:** pasta com PDFs, planilha de preços, FAQ, políticas  
**Depende do cliente:** sim — se demorar, o prazo desliza

### 2. Configurar namespace e ingerir base (Dia 1)

**Tempo:** 1-2h  
**Responsável:** Luiz  
**Comando:**

```bash
# Na VPS ou local com acesso ao banco
python -m app.cli.ingest --namespace <cliente> --path /data/<cliente>/docs/ --clear
```

**Validação:** rodar query direta no banco e conferir chunks:

```sql
SELECT count(*), source_file FROM knowledge_chunks WHERE namespace = '<cliente>' GROUP BY source_file;
```

### 3. Criar sessão de teste com agent_type=faq_rag (Dia 1)

**Tempo:** 15 min  
**Comando:**

```bash
curl -X POST https://<dominio>/api/sessions \
  -H 'Content-Type: application/json' \
  -d '{"niche": "<nicho_do_cliente>", "agent_type": "faq_rag"}'
```

**Validação:** enviar 3 perguntas e confirmar que responde com base nos docs ingeridos.

### 4. Testar handoff e limites (Dia 1-2)

**Tempo:** 30 min  
**Validação:**

- Pergunta fora da base → "vou verificar com a equipe"
- Pergunta sobre preço não documentado → não inventa
- Pedido de humano → encaminha
- Rate limit funciona
- Kill switch funciona

### 5. Configurar CONTACT_URL real (Dia 2)

**Tempo:** 10 min  
**Ação:** editar `.env` da VPS/container:

```
CONTACT_URL=https://wa.me/55<DDD><NUMERO_DO_CLIENTE>
```

### 6. Conectar WhatsApp Cloud API (Dia 2-3, se Pro/Business)

**Tempo:** 2-4h  
**Ação:** configurar webhook Meta → FastAPI/n8n.  
**Depende do cliente:** número verificado na Meta.

### 7. Validação final com cliente (Dia 3)

**Tempo:** 30 min  
**Ação:** call de 15 min mostrando o agente respondendo com a base do cliente.  
**Aceite:** cliente aprova ou solicita ajustes.

### 8. Go-live (Dia 3)

**Tempo:** 15 min  
**Ação:** ativar kill switch, monitorar 24h, confirmar operação.

## Checklist de entrega

- [ ] Documentos do cliente recebidos e convertidos para .md/.txt
- [ ] Base ingerida no namespace correto
- [ ] Sessão de teste funciona com RAG real
- [ ] Handoff funciona (pergunta fora da base → encaminha)
- [ ] CONTACT_URL configurado com número real do cliente
- [ ] Rate limit e guardrails ativos
- [ ] Cliente aprovou em call de validação
- [ ] Kill switch liberado para operação

## Rollback

Se algo der errado após go-live:

```bash
# Parar o agente
curl -X POST https://<dominio>/api/admin/killswitch -H 'Authorization: Bearer <token>' -d '{"chat": false}'

# Limpar base se necessário
python -m app.cli.ingest --namespace <cliente> --clear --path /dev/null
```
