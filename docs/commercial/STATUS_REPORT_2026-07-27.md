# Status Report Executivo — Atende AI / WhatsApp Agents

**Data:** 2026-07-27  
**Autor:** Claude (assistente técnico)  
**Para:** Luiz Felipe — Tech Lead IA / CTO Lufe Digital Wave  
**Projeto:** Atende AI / WhatsApp Agents  
**Produção:** https://atendeai.lufedigitalwave.com.br  
**GitHub:** https://github.com/LufeDigitalWave/atende-ai (público)  
**VPS:** 93.127.211.7 (EasyPanel + Traefik)  

---

## Resumo executivo

O Atende AI foi reposicionado de "demo SDR isolada" para **vitrine principal da linha WhatsApp Agents da Lufe Digital Wave**. Em uma sessão, entregamos 5 sprints completas: landing comercial, kit de vendas, página de pricing interativa, polimento de SEO e hardening de segurança. Tudo está em produção, validado e pronto para gerar propostas ativas.

---

## O que existe hoje

### Produto público em produção

| Rota | O que faz | Status |
| --- | --- | --- |
| `/` | Landing comercial WhatsApp Agents | ✅ produção |
| `/demo` | Demo interativa SDR com CRM ao vivo | ✅ produção |
| `/agentes` | Catálogo de 6 agentes com detalhes | ✅ produção |
| `/pricing` | Pacotes + simulador de custo interativo | ✅ produção |
| `/como-funciona` | Explicação demo versus produção + FAQ | ✅ produção |
| `/admin` | Admin interno (JWT, kanban, custos) | ✅ produção (protegido) |
| `/api/health` | Healthcheck da API | ✅ produção |

### Catálogo de agentes vendáveis

| Agente | Público | Diferencial |
| --- | --- | --- |
| SDR Agent | Empresas que recebem leads no WhatsApp | Qualifica, pontua, atualiza CRM em tempo real |
| Support Agent | SaaS, e-commerce, operações de alto volume | Consulta base RAG, abre ticket, handoff com contexto |
| Appointment Agent | Clínicas, estética, oficinas, serviços | Coleta disponibilidade, sugere horários, confirma |
| FAQ/RAG Agent | Empresas com documentos/políticas/catálogos | Responde com base autorizada, sem inventar |
| Civic Agent | Prefeituras, câmaras, ouvidorias | Classifica demanda, coleta endereço, gera protocolo |
| Collections Agent | Financeiro, cursos, serviços recorrentes | Cadência de follow-up, respeita opt-out, escala humano |

### Pacotes comerciais

| Pacote | Implantação | Mensalidade | Perfil |
| --- | ---: | ---: | --- |
| Starter | R$ 1.500–3.000 | R$ 300–800/mês | 1 agente, 1 fluxo, handoff |
| Pro | R$ 3.500–8.000 | R$ 800–2.000/mês | RAG, CRM/agenda, métricas |
| Business | R$ 8.000+ | R$ 2.000+/mês | Multiagente, integrações, operação |

---

## Stack técnica

| Camada | Tecnologia |
| --- | --- |
| Backend | FastAPI + SQLAlchemy async + Alembic |
| Frontend | React 18 + Vite + Tailwind + React Router + Lucide |
| DB | PostgreSQL 16 + pgvector (HNSW index) |
| LLM chat | OpenAI gpt-4o-mini (configurável para Claude Haiku 4.5) |
| LLM factory | OpenAI gpt-4.1-mini (CoT + few-shot) |
| Deploy | Docker Compose + EasyPanel + Traefik (HTTPS) |
| CI | GitHub Actions (ruff + pytest + vite build + vitest) |
| Testes | 115 backend + 7 unit frontend + 20 E2E Playwright |

---

## Arquitetura do agente (3 layers)

```text
Layer 1: Factory    → gera perfil de empresa fictícia por nicho (gpt-4.1-mini)
Layer 2: Renderer   → preenche template de prompt versionado (determinístico)
Layer 3: Runtime    → chat SSE + RAG + extração + scoring + FSM + handoff
```

Adicionar um nicho não exige criar prompt novo. A Factory gera dados, o Renderer monta o prompt, o Runtime executa.

---

## Sprints entregues nesta sessão (2026-07-24 a 2026-07-27)

### Sprint 1 — Vitrine WhatsApp Agents

**Objetivo:** Reposicionar o Atende AI de demo técnica para vitrine comercial vendável.

**Entregue:**

- Landing comercial em `/` com hero, prova técnica, catálogo resumido, diferenciais e CTA.
- Demo SDR preservada intacta em `/demo`.
- Catálogo completo em `/agentes` com 6 agents e fluxos.
- `/como-funciona` redesenhado com ícones Lucide e layout premium.
- Componentes de marketing reutilizáveis: SiteHeader, AgentCard, CTASection.
- URL de contato centralizada e validada com allowlist WhatsApp.
- Security review aplicado: telefone real removido do bundle público, admin escondido.
- README reposicionado como "Atende AI — WhatsApp Agents Demo".
- E2E novo para marketing (18/18 antes, 20/20 depois do pricing).

**Commits:** `a89a03c`, `0cd82a1`, `6e7975d`

### Sprint 2 — Kit Comercial

**Objetivo:** Criar materiais de venda para Luiz e sócio comercial.

**Entregue em `docs/commercial/`:**

- `pitch.md` — narrativa curta de 15s e 60s + mensagem para sócio.
- `proposta.md` — proposta-base para 99freelas/Workana/cliente direto.
- `pricing.md` — pacotes com lógica de preço e margem.
- `roteiro-demo.md` — roteiro de 5 minutos para call comercial.
- `checklist-venda.md` — discovery, qualificação e fechamento.
- `whatsapp-agents-pricing.xlsx` — calculadora com 3 abas: Calculadora, Pacotes, Custos LLM.
- `whatsapp-agents-pitch.pptx` — pitch deck de 8 slides dark premium.
- `screenshots/` — 7 capturas reais da produção (desktop + mobile).

**Commit:** `f5b12e4`

### Sprint 3 — Pricing Interativo + Demo GIF

**Objetivo:** Permitir que visitante simule custo e ter GIF para README/propostas.

**Entregue:**

- Página `/pricing` com 3 cards de pacotes, destaque visual no Pro.
- Simulador interativo: slider 100–5000 conversas/mês calcula custo LLM + infra em tempo real.
- FAQ de pricing com 4 perguntas comuns.
- Demo GIF de 5 frames (gravado via Playwright com mocks, montado com Pillow).
- README atualizado com GIF embed.
- Header com link "Pricing".
- Dados de pricing centralizados em `frontend/src/data/pricing.ts`.
- E2E cobrindo `/pricing` (20/20).

**Commit:** `30de6e1`

### Sprint 4 — SEO e Identidade Visual

**Objetivo:** Aparecer bem quando o link for compartilhado.

**Entregue:**

- Title: "Atende AI — Agentes de IA para WhatsApp".
- Meta description alinhada com WhatsApp Agents.
- Open Graph completo: título, descrição, URL canônica, imagem 1200x630, locale pt_BR, site_name.
- Twitter Card summary_large_image.
- `favicon.svg` — gradiente violet→cyan com "A" em branco.
- `apple-touch-icon.png` — 180x180.
- `og-image.png` — 1200x630 com marca e agentes.
- Canonical URL.

**Commit:** `61f8dec`

### Sprint 5 — Hardening Final

**Objetivo:** Segurança, indexação e cache corretos para produção pública.

**Entregue:**

- `robots.txt` permitindo indexação + referência ao sitemap.
- `sitemap.xml` com 5 rotas públicas priorizadas.
- CSP expandida: `frame-ancestors 'self'`, img-src com domínio OG.
- `X-DNS-Prefetch-Control: on`.
- Cache headers: `no-cache` para index.html, `immutable 30d` para assets.
- Fix: security headers restaurados em location blocks (nginx override corrigido).

**Commits:** `b5ccd58`, `b771c11`, `b1f5db2`

---

## Segurança em produção

| Header | Valor |
| --- | --- |
| Content-Security-Policy | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://atendeai.lufedigitalwave.com.br; connect-src 'self' https:; font-src 'self' data:; frame-ancestors 'self';` |
| Strict-Transport-Security | `max-age=31536000; includeSubDomains` |
| X-Content-Type-Options | `nosniff` |
| X-Frame-Options | `SAMEORIGIN` |
| Referrer-Policy | `strict-origin-when-cross-origin` |
| Permissions-Policy | `geolocation=(), microphone=(), camera=()` |
| X-DNS-Prefetch-Control | `on` |
| Cache-Control (index.html) | `no-cache, no-store, must-revalidate` |
| Cache-Control (assets) | `public, immutable` + expires 30d |

Medidas adicionais:

- Telefone real removido do bundle público; fallback usa número fictício.
- `getSafeContactUrl()` valida apenas hosts `wa.me` e `api.whatsapp.com`.
- Backend `contact_url` validado por Pydantic (allowlist de hosts HTTPS).
- Admin credenciais hint só aparece em `import.meta.env.DEV`.
- Admin não exposto no README público.
- JWT secret e admin password validados com mínimo em produção (fail-fast no startup).
- PII sanitizer em logs de produção.

---

## Guardrails operacionais

| Guardrail | Configuração |
| --- | --- |
| Cap por sessão | 30 mensagens |
| Rate limit | 2s entre mensagens + 5 sessões/IP/h |
| Budget diário | 200k tokens com alerting webhook |
| Input max | 500 caracteres |
| Session TTL | 24h com soft delete |
| Kill switch | Toggle no admin sem restart |
| Reset noturno | Container cron para soft delete + reseed |

---

## Validações executadas

| Validação | Resultado |
| --- | --- |
| Frontend build (Vite) | ✅ passa |
| Frontend unit tests (Vitest) | ✅ 7/7 |
| Frontend E2E (Playwright) | ✅ 20/20 |
| Backend tests (pytest) | ✅ 115 passed, 9 xfailed |
| Visual smoke desktop 1440x1000 | ✅ todas as rotas |
| Visual smoke mobile 375x812 | ✅ sem overflow horizontal |
| Visual produção real (Playwright) | ✅ conteúdo esperado |
| Security headers produção | ✅ todos presentes |
| robots.txt produção | ✅ 200 |
| sitemap.xml produção | ✅ 200 |
| favicon.svg produção | ✅ 200 |
| og-image.png produção | ✅ 200 |
| API health produção | ✅ `{"status":"ok"}` |
| Code review (5 ângulos) | ✅ achados corrigidos |
| Security review | ✅ achados corrigidos |

---

## Materiais comerciais prontos

| Material | Formato | Local |
| --- | --- | --- |
| Pitch (15s + 60s + sócio) | Markdown | `docs/commercial/pitch.md` |
| Proposta-base (99freelas/Workana) | Markdown | `docs/commercial/proposta.md` |
| Pricing e lógica de pacotes | Markdown | `docs/commercial/pricing.md` |
| Roteiro de demo (5 min) | Markdown | `docs/commercial/roteiro-demo.md` |
| Checklist de venda | Markdown | `docs/commercial/checklist-venda.md` |
| Calculadora de pricing | XLSX (3 abas) | `docs/commercial/whatsapp-agents-pricing.xlsx` |
| Pitch deck | PPTX (8 slides) | `docs/commercial/whatsapp-agents-pitch.pptx` |
| Screenshots produção | 7 PNG | `docs/commercial/screenshots/` |
| Demo animado | GIF (5 frames) | `docs/commercial/demo.gif` |

---

## Arquivos principais do frontend (pós-5 sprints)

```text
frontend/
├── public/
│   ├── favicon.svg
│   ├── apple-touch-icon.png
│   ├── og-image.png
│   ├── robots.txt
│   └── sitemap.xml
├── src/
│   ├── App.tsx                         # Landing WhatsApp Agents
│   ├── main.tsx                        # Rotas: /, /demo, /agentes, /pricing, /como-funciona, /admin
│   ├── data/
│   │   ├── agents.ts                   # Catálogo 6 agentes
│   │   └── pricing.ts                  # Pacotes + constantes LLM
│   ├── lib/
│   │   ├── constants.ts                # CONTACT_URL + allowlist + helpers
│   │   ├── api.ts                      # API client SSE
│   │   └── store.ts                    # Zustand state
│   ├── pages/
│   │   ├── Demo.tsx                    # Demo SDR preservada
│   │   ├── Agentes.tsx                 # Catálogo completo
│   │   ├── Pricing.tsx                 # Pacotes + simulador
│   │   ├── ComoFunciona.tsx            # Explicação demo→produção
│   │   └── Admin.tsx                   # Admin (dica dev-only)
│   └── components/
│       ├── marketing/
│       │   ├── SiteHeader.tsx
│       │   ├── AgentCard.tsx
│       │   └── CTASection.tsx
│       ├── chat/
│       │   └── ChatWindow.tsx          # buildWhatsAppContactUrl
│       └── crm/
├── e2e/
│   ├── marketing.spec.ts              # Landing + agentes + pricing
│   ├── chat.spec.ts                   # Fluxo chat
│   └── chat-mobile.spec.ts            # Mobile layout
├── nginx.conf                          # Security headers + cache + proxy
├── Dockerfile                          # Multi-stage (Node build → nginx)
└── index.html                          # Meta tags OG/Twitter + canonical
```

---

## Onde tudo está salvo

| Local | O que contém |
| --- | --- |
| GitHub `main` | Código completo, docs, changelog, commercial kit |
| VPS `/opt/atende-ai` | Deploy atualizado, containers rodando |
| Memória Claude `project_atende_ai.md` | Estado completo do projeto com todas sprints |
| Memória Claude `MEMORY.md` | Índice atualizado |
| `docs/commercial/` | Kit de vendas pronto para uso |
| `docs/CHANGELOG.md` | Histórico de todas as mudanças |
| `docs/REVIEW.md` | Validações Sprint 1 registradas |

---

## O que NÃO foi feito (fora de escopo até agora)

- Agentes secundários (Support, Appointment, etc.) funcionais — só existem como catálogo.
- Landing em subdomínio separado (`whatsapp-agents.lufedigitalwave.com.br`).
- Backend de billing/pagamento real.
- Checkout ou integração Asaas/Stripe.
- Dashboard de métricas para o cliente.
- Campanhas WhatsApp ativas (templates Meta).
- Integração real com CRM externo (Kommo, HubSpot).
- Testes de carga.
- Migração de LLM para Claude consolidado.
- Sentry/observabilidade em produção.

---

## Próximos passos recomendados

### Imediato (esta semana)

1. **Enviar propostas ativas** usando materiais + link pricing + demo.
2. **Testar roteiro** em primeira call real com sócio comercial.
3. **Monitorar CI** do GitHub após push de main.

### Curto prazo (próximas 2 semanas)

4. **Fechar primeiro piloto** Starter com cliente real.
5. **Gerar vídeo curto** (Loom ou gravação de tela) do fluxo da demo.
6. **Ativar LLM real** em produção se fizer call com cliente (atualmente em `openai` mode).

### Médio prazo (30 dias)

7. **Sprint 6:** Dashboard de métricas para acompanhar demo usage.
8. **Sprint 7:** Implementar 1 agente secundário funcional (Appointment ou Support) para expandir demo.
9. **Migrar LLM** para Claude Haiku 4.5 com prompt caching (economia estimada 60-80%).
10. **Ativar Sentry** para observabilidade em produção.

---

## Números para usar em propostas

- 30+ projetos de IA/automação entregues em 3 anos.
- 70+ workflows n8n ativos em produção simultânea.
- 142 testes automatizados (115 backend + 7 frontend + 20 E2E).
- Zero banimentos com API oficial Meta em 3 anos.
- Demo pública com CRM ao vivo: https://atendeai.lufedigitalwave.com.br
- Custo por conversa: R$ 0,02 a R$ 0,05 com Claude Haiku + caching.
- Setores validados: saúde, jurídico, agro, imóveis, eventos, educação, marketing, contabilidade, estética, governo, food service, e-commerce, seguros.

---

**Conclusão:** O Atende AI está pronto para vender. A vitrine funciona, o kit comercial está montado, os pacotes estão definidos e a produção está segura. O próximo passo é ação comercial: propostas, calls e fechamento do primeiro piloto.
