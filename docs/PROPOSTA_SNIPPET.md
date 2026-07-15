# Snippet de Proposta — Atende AI

> Duas versões: curta pra 99Freelas (~400 chars) e média pra Workana (~700 chars).
> Substitua `{LINK_DEMO}` e `{LINK_REPO}` pelos seus links reais antes de colar.

---

## Versão A — 99Freelas (~400 chars)

```
Agente SDR de IA no WhatsApp oficial da sua empresa — qualifica leads,
agenda avaliações e entrega pro vendedor certo, 24/7.

Tecnologia: Claude API + RAG (base de conhecimento da sua empresa) +
extração estruturada + CRM em tempo real.

• Responde dúvidas com sua base (não alucina preço)
• Coleta campos automaticamente (nome, serviço, orçamento)
• Escala pra humano quando precisa
• Custo: ~R$ 0,03 por conversa em haiku + R$ 80/mês infra
• Setup: 1–2 semanas com sua base

Veja funcionando: {LINK_DEMO}
Código aberto: {LINK_REPO}

Posso demonstrar na sua call?
```

---

## Versão B — Workana (~700 chars)

```
Olá! Sou especialista em agentes de IA conversacional pra SDR e atendimento
no WhatsApp oficial.

A dor que resolvo: leads que chegam fora de horário, vendedores gastando 1h
qualificando antes de falar com o cliente, perda de oportunidade por demora
na resposta.

A solução: agente de IA que conversa em PT-BR natural, consulta a base de
conhecimento da sua empresa (não inventa!), coleta os campos de qualificação
automaticamente, agenda avaliação e dispara handoff pro vendedor certo.
Tudo com prompt versionado, RAG com pgvector, guarda-corpos de custo e
dashboard de auditoria.

Diferenciais:
- Custo controlado: ~R$ 0,03 por conversa em haiku (Claude API)
- Cap diário + rate limit: você nunca estoura budget sem aviso
- Prompt versionado em arquivo — toda mudança tem changelog
- Funciona offline em modo roteirizado (testes e fallback)
- UI estilo chat responsiva (375px a 1440px)

Stack: FastAPI + Postgres + pgvector + React + Vite + Docker.

Veja a demo ao vivo: {LINK_DEMO}
Repositório aberto (anonimizado pra portfólio): {LINK_REPO}

Posso agendar 20min pra eu mostrar funcionando e você ver o lead entrando
no CRM em tempo real?
```

---

## Customização por nicho

### Clínica de estética / saúde
> "Em vez de você pagar atendente jr pra fazer triagem de 'quanto custa botox',
> a IA faz 24/7 com RAG nos seus preços e agenda avaliação com a vendedora.
> Demonstração no link."

### Imobiliária
> "Lead chega às 23h querendo alugar apartamento de 3 quartos no centro.
> A IA qualifica (faixa de aluguel, prazo de mudança, tipo de imóvel), agenda
> visita com o corretor da região e manda push pro WhatsApp dele. Você só
> aparece na hora certa."

### Escritório de advocacia
> "Lead manda 'foi demitido, tenho quanto tempo pra entrar com ação?'.
> A IA coleta área do direito, urgência, valor da causa, e agenda consulta
> com o advogado especialista. Sem PII exposta."

### SaaS B2B
> "Lead técnico pede demo. A IA qualifica stack atual, tamanho da empresa,
> budget range e caso de uso. Só manda pra SDR humano quando
> orçamento ≥ R$ X. SDR fala com lead quente, não com curioso."

### E-commerce
> "Lead manda 'o produto X tem garantia?'. A IA responde (RAG), sugere
> produtos complementares, fecha pedido e manda link de pagamento.
> Devolução/reclamação → handoff pra humano."

---

## Anti-padrões a evitar

- **NUNCA** mencionar ChatGPT, GPT, OpenAI na proposta — falar só em "Claude API" ou "modelo de IA proprietário".
- **NUNCA** prometer "100% dos casos resolvidos" — falar em "80% das conversas qualificadas sem humano".
- **NUNCA** colocar preço fixo por conversa na proposta — falar em "faixa de R$ 0,02–0,05".
- **SEMPRE** mandar link da demo primeiro, proposta depois.
- **SEMPRE** terminar com pergunta de call, nunca com "te aviso".