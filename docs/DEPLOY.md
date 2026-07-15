# Deploy — Atende AI

> Guia rápido pra subir a demo numa VPS via Easypanel + Traefik.

---

## Opção A — Easypanel (recomendado pra demo/MVP)

### 1. Pré-requisitos
- VPS com Easypanel instalado (Ubuntu 22.04 / 2 GB RAM mínimo).
- Domínio apontando pra VPS (A record).
- Subdomínios: `demo.seudominio.com` (frontend), `api.seudominio.com` (backend).

### 2. Criar projeto
1. EasyPanel → New Project → name: `atende-ai`.
2. Add Service → App:
   - Source: GitHub repo `LufeDigitalWave/atende-ai`.
   - Build path: `/`.
   - Dockerfile: `./Dockerfile.web` (criar wrapper que aponta pra `frontend/Dockerfile`).

### 3. Variáveis de ambiente (no painel)
Copie do `.env.example` e preencha:
- `LLM_PROVIDER=claude`
- `ANTHROPIC_API_KEY=...`
- `EMBEDDING_PROVIDER=fake` (ou `voyage` se tiver)
- `POSTGRES_PASSWORD=<senha-forte>`
- `ADMIN_PASSWORD=<senha-forte>`
- `JWT_SECRET=<openssl rand -hex 32>`
- `DAILY_TOKEN_BUDGET=200000`
- `CONTACT_URL=https://wa.me/55...`
- `VITE_API_URL=https://api.seudominio.com`

### 4. Postgres
- Add Service → Database → PostgreSQL 16 + pgvector.
- Aponte `DATABASE_URL` pro serviço interno.

### 5. Cron de reset
- Adicione um terceiro serviço com a mesma imagem do backend.
- Command: `while true; do sleep 86400; python -m app.services.reset; done`.
- Ou use um cron externo (EasyPanel tem Cron Jobs).

### 6. HTTPS / Traefik
- Easypanel já configura Traefik automaticamente.
- Frontend: domínio público, serve estático do nginx.
- Backend: domínio público, proxy_pass pra uvicorn na 8000.

### 7. Primeiro start
1. Faça deploy.
2. Acompanhe logs do `api` — deve ver "alembic upgrade head" e "seed complete".
3. Acesse `https://demo.seudominio.com` e teste o roteiro do `DEMO.md`.

---

## Opção B — Docker Compose manual (VPS limpa)

### 1. Instalar
```bash
# VPS Ubuntu 22.04+
apt update && apt install -y docker.io docker-compose-plugin
git clone https://github.com/LufeDigitalWave/atende-ai.git
cd atende-ai
cp .env.example .env
nano .env  # preencher
```

### 2. Subir
```bash
docker compose up -d
docker compose logs -f api   # acompanhar seed
```

### 3. Reverse proxy (nginx + certbot)
```nginx
# /etc/nginx/sites-available/atende
server {
  server_name demo.seudominio.com;
  location / {
    proxy_pass http://127.0.0.1:5173;
  }
}

server {
  server_name api.seudominio.com;
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_buffering off;  # importante pra SSE!
    proxy_cache off;
  }
}
```

```bash
certbot --nginx -d demo.seudominio.com -d api.seudominio.com
```

**Importante**: SSE precisa de `proxy_buffering off` e `proxy_cache off`. Sem isso, o stream fica chunked e atrasado.

### 4. Cron de reset (sistema)
```bash
crontab -e
# 03:00 todo dia, em horário de SP
0 3 * * * TZ=America/Sao_Paulo docker compose -C /root/atende-ai run --rm api python -m app.services.reset
```

---

## Checklist de budget

Antes de abrir pro público:

- [ ] `DAILY_TOKEN_BUDGET` definido (default 200k é seguro).
- [ ] `CONTACT_URL` apontando pro SEU contato (não da empresa fictícia).
- [ ] Banner "high_demand" testado (mude `DAILY_TOKEN_BUDGET=1000` por 5 min pra forçar).
- [ ] Reset noturno ativo (cron ou container `reset`).
- [ ] Logs com `LOG_LEVEL=INFO` em prod (não DEBUG).

---

## Monitoramento

### Logs
- `docker compose logs -f api` — fluxo principal.
- `docker compose logs -f reset` — prune diário.
- `docker compose logs -f db` — só pra erros.

### Métricas simples
- Tamanho do banco: `docker exec atende_db psql -U atende -d atende_ai -c "SELECT pg_size_pretty(pg_database_size('atende_ai'));"`
- Tokens de hoje: rota `/admin/custos`.
- Sessões ativas: rota `/admin/conversas`.

### Alertas (opcional, n8n + Telegram)
- Webhook no admin que manda alerta diário às 09h com custo de ontem.
- Alerta imediato se `usage_log` ultrapassar 50% do budget antes das 18h.

---

## Backup

### Banco
```bash
# diário, 03h30 (antes do reset)
30 3 * * * docker exec atende_db pg_dump -U atende atende_ai | gzip > /backup/atende-$(date +\%Y\%m\%d).sql.gz
```

Restauração:
```bash
gunzip -c backup.sql.gz | docker exec -i atende_db psql -U atende -d atende_ai
```

### Prompt e config
- Versionado no Git.
- `docs/AGENT_PROMPT.md` no repo.

---

## Troubleshooting de deploy

| Sintoma | Causa provável | Solução |
|---|---|---|
| SSE atrasa / chunked | nginx proxy_buffering on | Adicionar `proxy_buffering off` |
| CORS bloqueia | `VITE_API_URL` errado | Conferir `main.py` CORS origins |
| Budget estoura em 1h | Viralização ou abuse | Checar `usage_log` por IP; reduzir `DAILY_TOKEN_BUDGET` temporariamente |
| Reset não roda | Container parado ou TZ errado | `docker compose up reset`; `TZ=America/Sao_Paulo` no env |
| `relation "vector" does not exist` | pgvector não habilitado | Imagem `pgvector/pgvector:pg16` (não `postgres:16`) |
| Auth admin falha | `JWT_SECRET` mudou entre deploys | Resetar sessão; documentar pra equipe |

---

## Custos de infraestrutura

| Componente | Custo/mês |
|---|---|
| VPS Easypanel (2 GB, 1 vCPU) | R$ 30–60 |
| Domínio | R$ 5 |
| Claude API (300 conversas/mês) | R$ 8 |
| **Total demo** | **~R$ 50–70/mês** |

Em produção real, some o custo de atendente jr (~R$ 5.000) e multiplique por escala.