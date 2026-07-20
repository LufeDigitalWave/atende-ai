# Deploy na VPS — Atende AI

> Template público de deploy. Substitua `<VPS_IP>`, `<APP_DOMAIN>`, `<SSH_USER>`, `<ORG>` e `<APP_DIR>` pelos valores reais do seu ambiente local/privado antes de executar.
>
> Instruções passo-a-passo para fazer deploy da demo na VPS `<VPS_IP>` com nginx + certbot.

## Pré-requisitos

- VPS: Ubuntu 22.04+ com Docker/Swarm instalado
- SSH acesso: `<SSH_USER>@<VPS_IP>`
- Domínio: `<APP_DOMAIN>` apontando para `<VPS_IP>` ✅
- OpenAI API key (pra factory gpt-4.1-mini)
- Anthropic API key (pra agent claude-haiku-4-5)

---

## 1. SSH na VPS

```bash
ssh <SSH_USER>@<VPS_IP>
```

---

## 2. Clonar o repositório

```bash
cd /opt
git clone https://github.com/<ORG>/atende-ai.git
cd atende-ai
```

---

## 3. Criar `.env` com credenciais

```bash
cat > .env << 'EOF'
# Core
ENVIRONMENT=production
LOG_LEVEL=INFO
CONTACT_URL=https://wa.me/5511999999999

# Database
POSTGRES_USER=atende
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_DB=atende_ai
DATABASE_URL=postgresql+asyncpg://atende:${POSTGRES_PASSWORD}@db:5432/atende_ai

# LLM — Agent chat
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-XXXXX  # Preencher com chave real
AGENT_MODEL=claude-haiku-4-5
AGENT_TEMPERATURE=0.4

# LLM — Factory (niche profile generation)
FACTORY_MODEL=gpt-4.1-mini
OPENAI_API_KEY=sk-XXXXX  # Preencher com chave real
FACTORY_MAX_NICHE_CHARS=60

# Embeddings
EMBEDDING_PROVIDER=fake

# Budget / guards
DAILY_TOKEN_BUDGET=200000
MAX_MESSAGES_PER_SESSION=30
RATE_LIMIT_SECONDS=2
RATE_LIMIT_NEW_SESSIONS_PER_IP_HOUR=5
MAX_INPUT_CHARS=500
SESSION_TTL_HOURS=24

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$(openssl rand -hex 16)
JWT_SECRET=$(openssl rand -hex 32)
JWT_EXPIRES_HOURS=24

# Frontend (build-time)
VITE_API_URL=https://<APP_DOMAIN>

# CORS
CORS_ORIGINS=https://<APP_DOMAIN>
EOF
```

Substituir as chaves (`ANTHROPIC_API_KEY` e `OPENAI_API_KEY`) pelas reais.

---

## 4. Build das imagens Docker

```bash
docker build -t atende-ai-api:latest ./backend
docker build -t atende-ai-web:latest ./frontend
```

---

## 5. Criar rede Docker (Swarm mode)

```bash
docker swarm init  # Se não estiver em swarm yet
docker network create --driver overlay atende_net
```

---

## 6. Deploy do Postgres + pgvector

```bash
docker service create \
  --name atende_db \
  --network atende_net \
  --env POSTGRES_USER=atende \
  --env POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d= -f2) \
  --env POSTGRES_DB=atende_ai \
  --mount type=volume,source=atende_pgdata,target=/var/lib/postgresql/data \
  --constraint 'node.role == manager' \
  pgvector/pgvector:pg16
```

---

## 7. Deploy da API FastAPI

```bash
docker service create \
  --name atende_api \
  --network atende_net \
  --publish 8002:8000 \
  --env-file .env \
  --constraint 'node.role == manager' \
  --update-delay 10s \
  atende-ai-api:latest
```

---

## 8. Deploy do Frontend React

```bash
docker service create \
  --name atende_web \
  --network atende_net \
  --publish 5175:80 \
  --env VITE_API_URL=https://<APP_DOMAIN> \
  --constraint 'node.role == manager' \
  atende-ai-web:latest
```

---

## 9. Configurar nginx reverse proxy

```bash
cat > /etc/nginx/sites-available/atendeai << 'EOF'
upstream api_backend {
    server 127.0.0.1:8002;
}

upstream web_frontend {
    server 127.0.0.1:5175;
}

server {
    listen 80;
    server_name <APP_DOMAIN>;

    # Redirect HTTP → HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name <APP_DOMAIN>;

    ssl_certificate /etc/letsencrypt/live/<APP_DOMAIN>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<APP_DOMAIN>/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend
    location / {
        proxy_pass http://web_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # IMPORTANTE: SSE requer buffering=off
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection upgrade;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/atendeai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 10. Certificado SSL com certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d <APP_DOMAIN>
```

---

## 11. Verificar deploy

```bash
# Ver serviços rodando
docker service ls

# Ver logs da API
docker service logs atende_api -f

# Ver logs do Postgres
docker service logs atende_db -f

# Testar acesso
curl https://<APP_DOMAIN>/api/health
```

Esperado:
```json
{
  "status": "ok",
  "environment": "production",
  "provider": "claude",
  "timestamp": "2026-07-15T..."
}
```

---

## 12. Cron de reset noturno (opcional)

```bash
# Agendar reset diário às 03:00
crontab -e

# Adicionar:
0 3 * * * cd /opt/<APP_DIR> && docker run --rm --network atende_net -e DATABASE_URL="postgresql+asyncpg://atende:$(grep POSTGRES_PASSWORD .env | cut -d= -f2)@db:5432/atende_ai" atende-ai-api:latest python -m app.services.reset
```

---

## Troubleshooting

| Sintoma | Causa | Solução |
|---|---|---|
| `connection refused` na API | Postgres não pronto | Aguardar 30s e retry |
| SSE atrasa / chunked | nginx proxy_buffering on | Verificar nginx.conf (buffering off) |
| CORS bloqueia | CORS_ORIGINS mismatch | Conferir .env |
| Budget excedido | Viralização | Reduzir DAILY_TOKEN_BUDGET temporariamente |

---

## Monitoramento

```bash
# Tamanho do banco
docker exec atende_db psql -U atende -d atende_ai -c "SELECT pg_size_pretty(pg_database_size('atende_ai'));"

# Sessões ativas
curl https://<APP_DOMAIN>/admin/conversas  # com auth JWT

# Tokens de hoje
curl https://<APP_DOMAIN>/admin/custos  # com auth JWT
```

---

## Rollback

Se algo der errado:

```bash
# Parar tudo
docker service rm atende_api atende_web atende_db

# Remover volume de dados (se necessário)
docker volume rm atende_pgdata

# Voltar para estado anterior do git
git reset --hard HEAD~1
```
