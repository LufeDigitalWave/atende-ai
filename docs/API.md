# API Reference — Atende AI

> FastAPI backend. Todas as respostas JSON. Streaming via SSE (`text/event-stream`).

Base URL local: `http://localhost:8000`

---

## Endpoints públicos (demo)

### `GET /api/health`

Healthcheck simples.

**Response 200**
```json
{"status": "ok", "env": "development", "provider": "fake"}
```

### `POST /api/sessions`

Cria nova sessão. Anexa IP hasheado.

**Response 200**
```json
{
  "session_id": "uuid-v4",
  "created_at": "2026-07-13T12:34:56Z",
  "status": "active"
}
```

### `GET /api/sessions/{id}`

Retorna estado atual da sessão (mensagens + lead + eventos).

**Response 200**
```json
{
  "session_id": "uuid",
  "status": "active",
  "message_count": 4,
  "messages": [
    {"role": "user", "content": "...", "created_at": "..."},
    {"role": "agent", "content": "...", "created_at": "..."}
  ],
  "lead": {
    "name": null,
    "service_interest": "melasma",
    "complaint": "manchas no rosto",
    "budget_range": "ate_3k",
    "urgency": "alta",
    "score": 80,
    "state": "em_qualificacao"
  },
  "events": [
    {"type": "service_identified", "payload": {"service": "melasma"}, "created_at": "..."}
  ]
}
```

### `POST /api/sessions/{id}/messages`

Envia mensagem do visitante. **Inicia SSE imediatamente**: retorna `Content-Type: text/event-stream` com a stream de tokens da Sofia + eventos do CRM.

**Request body**
```json
{"content": "oi, quanto custa tratar melasma?"}
```

**Erros**
- `400` — input > 500 chars
- `404` — sessão inexistente
- `410` — sessão capped/expired
- `429` — rate limit (1 msg/2s)
- `503` — budget diário estourado (`{"banner": "high_demand", "url": "..."}`)

**SSE stream (event: data)**
```
event: typing
data: {"active": true}

event: token
data: {"delta": "Oi"}

event: token
data: {"delta": "! "}

event: token
data: {"delta": "Que bom te ver por aqui 😊"}

event: lead_update
data: {"fields": {"service_interest": "melasma"}}

event: score_update
data: {"total": 20, "breakdown": {"service_interest": 20}}

event: state_update
data: {"from": "novo", "to": "em_qualificacao"}

event: timeline_event
data: {"type": "service_identified", "payload": {"service": "melasma"}}

event: done
data: {"latency_ms": 1234, "message_id": "uuid"}
```

### `GET /api/sessions/{id}/events`

Conecta só no SSE (sem enviar mensagem). Útil pro frontend que perdeu conexão.

Mesmos eventos do stream acima, exceto `token`.

---

## Endpoints admin

Todos exigem header `Authorization: Bearer <jwt>`.

### `POST /api/admin/login`

**Request**
```json
{"username": "admin", "password": "..."}
```

**Response 200**
```json
{"token": "eyJ...", "expires_at": "2026-07-14T12:34:56Z"}
```

**Errors** — `401` (credenciais), `429` (> 5 tentativas em 15min do mesmo IP).

### `GET /api/admin/conversas`

Lista paginada de sessões.

**Query**: `?limit=20&offset=0&status=active`

**Response 200**
```json
{
  "total": 47,
  "items": [
    {
      "session_id": "uuid",
      "created_at": "...",
      "last_activity_at": "...",
      "message_count": 12,
      "status": "active",
      "lead_name": "João",
      "lead_state": "qualificado",
      "lead_score": 80
    }
  ]
}
```

### `GET /api/admin/conversas/{id}`

Detalhe de uma sessão (mesmo payload de `GET /api/sessions/{id}`).

### `GET /api/admin/leads`

Kanban-ready: agrupa por `state`.

**Response 200**
```json
{
  "novo": [{"lead_id": "...", "name": "João", "score": 80, ...}],
  "em_qualificacao": [...],
  "qualificado": [...],
  "agendamento_proposto": [...],
  "handoff": [...]
}
```

### `GET /api/admin/custos?days=14`

**Response 200**
```json
{
  "today": {
    "calls": 27,
    "input_tokens": 8420,
    "output_tokens": 3340,
    "cached_tokens": 5120,
    "cost_usd": 0.0187,
    "cost_brl": 0.094
  },
  "history": [
    {"date": "2026-07-01", "calls": 19, "cost_brl": 0.067},
    ...
  ],
  "budget": {
    "daily_tokens": 200000,
    "used_today": 11760,
    "percent_used": 5.88
  }
}
```

### `GET /api/admin/agente`

**Response 200**
```json
{
  "provider": "claude",
  "model": "claude-haiku-4-5",
  "prompt_version": "sofia_v1",
  "prompt_sha256": "abc123...",
  "temperature": 0.4,
  "embedding_provider": "fake",
  "embedding_model": null
}
```

---

## SSE — formato de evento

Todo evento SSE segue:
```
event: <event_name>
data: <json>

```

(Mesma spec do W3C. Frontend usa `EventSource` ou `fetch` + reader.)

---

## Erros globais

| Status | Quando |
|---|---|
| 400 | Body inválido, input > 500 chars |
| 401 | JWT ausente / expirado em rota admin |
| 404 | Sessão inexistente |
| 410 | Sessão capped/expired |
| 429 | Rate limit (sessão ou IP) |
| 503 | Budget diário estourado |

Formato de erro:
```json
{"detail": "Mensagem humana", "code": "rate_limit"}
```