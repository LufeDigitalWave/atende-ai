# Roteiro de Demo — Atende AI

> Documento **operacional** pra você (vendedor). 5 minutos, do zero ao fechamento.
> Duração alvo: **4–6 min** + 2–3 min de objeções.

---

## Antes da call

1. Abra duas abas lado a lado: demo `/` e admin `/admin` já logado.
2. Limpe sessão anterior (botão discreto no header admin: "Reset demo" — não aparece pro visitante).
3. Tenha em mãos `PROPOSTA_SNIPPET.md` (proposta comercial) e `COST_MODEL.md` (estimativa de custo).
4. ZOOM 100% no navegador; áudio off (a demo não tem som).

---

## Passo a passo (5 min)

### 1. Abertura (15 s)

> *"Antes de eu explicar como funciona, deixa eu te mostrar funcionando. Você é o cliente — abre a demo aqui do lado e conversa com a Sofia, que é a SDR da Clínica Renova. Olha o CRM aqui do lado — vai preenchendo sozinho."*

Mande o cliente abrir a demo em modo **fake** primeiro (mais rápido), ou **claude** se quiser impressionar com resposta natural.

### 2. Gatilho de "uau" #1 — extração visível (60 s)

**Você fala como cliente:**

> "Oi, vi o anúncio de vocês, quanto custa tratar melasma?"

**Aponta pro CRM:**

> "Repara que o campo 'serviço de interesse' já preencheu sozinho. E o score já subiu de 0 pra 20 — porque um campo foi identificado. Tudo isso sem o visitante preencher formulário nenhum."

### 3. Gatilho de "uau" #2 — multi-campo oportunístico (60 s)

**Numa frase só:**

> "Meu nome é João, quero resolver manchas no rosto, posso investir uns 3 mil reais e queria começar logo."

**Aponta:**

> "Olha — em **uma** mensagem, quatro campos preencheram: nome, serviço, queixa e orçamento. E o score pulou pra 80. Sabe qual o truque? O prompt da Sofia não faz interrogatório — ela extrai o que vier, na ordem que vier."

### 4. Pergunta de FAQ — RAG em ação (45 s)

> "Vocês atendem sábado?"

**Aponta:**

> "Ela não chutou. Olha a resposta — veio direto da base de conhecimento. E a conversa volta pra qualificação sem você precisar puxar."

### 5. Fechamento do funil — handoff + agendamento (60 s)

> "Pode ser, me agendem na próxima quinta de manhã."

**Aponta:**

> "Apareceram 3 botões de horário. Toca em um e olha — evento na timeline, estado mudou pra 'agendamento_proposto', lead marcado como 'qualificado', vendedora fictícia Paula foi notificada. Em produção, esse mesmo evento sai daqui e vai pro HubSpot ou Kommo do cliente."

### 6. Custo real (30 s)

Abra o admin → aba Custos:

> *"Essa conversa que você acabou de ver custou R$ 0,0X. Em haiku com prompt caching, fica nessa faixa. Multiplica por 1000 conversas/mês e você tem o custo do atendente — que é 1% do salário de um humano fazendo a mesma triagem."*

### 7. Frase de fechamento (20 s)

> *"Isso que você testou é o mesmo motor que eu coloco no WhatsApp oficial da sua empresa, com a sua base de conhecimento e o seu CRM. A Clínica Renova é fictícia — mas o agente, o RAG, a extração e o funil são reais e eu entrego pronto."*

Pause. Deixe o cliente falar.

---

## Objeções mapeadas

### "A IA inventa coisas / alucina preço"

> "Resposta em 3 camadas. **1)** Preço e informações clínicas vêm de uma base RAG com os dados da empresa — a IA não inventa, ela lê. **2)** O prompt tem regra explícita: 'se não estiver na base, diga que vai confirmar'. **3)** Toda resposta é auditável — você vê o trecho da base que ela usou, antes de ir pro cliente. Em produção a gente liga um log de fontes em cada resposta."

### "Quanto custa por mês?"

Aponta pra `docs/COST_MODEL.md`:
> "Depende do volume. Pra 500 conversas/mês em haiku, ordem de R$ 25–40 em API. Soma a infraestrutura (Postgres + API num VPS) e fica na faixa de R$ 100–150/mês tudo. Comparado a um atendente jr em CLT, é menos de 5% do custo."

### "Quanto tempo pra colocar na minha empresa?"

> "1 semana pro MVP funcional com a sua base. **2 semanas** se você quer integrações (CRM, agenda real, Meta Cloud API). A Clínica Renova é genérica justamente porque o motor é o mesmo — o que muda é a base de conhecimento e os campos de qualificação."

### "E se o cliente xingar a IA / pedir humano?"

> "Detecção automática de 5 frases-chave ('quero falar com humano', 'atendente', 'pessoa real', etc) → handoff imediato. A IA também registra tom hostil na timeline pra equipe revisar depois. Em produção a gente adiciona as suas frases-chave específicas."

### "Funciona em outros idiomas?"

> "Sim — o prompt é em PT-BR porque o público é brasileiro, mas troca o system prompt e a base RAG e roda em qualquer idioma. Mesmo motor."

### "E se cair a internet / a API da Anthropic?"

> "A demo cai num `FakeLLMProvider` roteirizado — sempre responde, mesmo offline. Em produção a gente adiciona fallback por regra e fila de mensagens pra reenviar quando volta."

### "Posso treinar com dados meus?"

> "Sim. Em produção você sobe a sua base (PDFs, docs, planilha de preços) e a gente re-ingeriu no RAG. **Você nunca treina modelo** — só atualiza base. Mudou preço de serviço, atualiza 1 arquivo."

### "Funciona no Instagram Direct / Telegram / site?"

> "O motor é o mesmo. Em produção a gente pluga no canal que você quiser (Meta Cloud API, Telegram Bot, widget do site). A demo é por uma interface web justamente porque é onde **qualquer** pessoa pode abrir sem instalar nada."

---

## Dicas de postura

- **Não leia o roteiro.** Use como checklist. Olho no olho do cliente.
- **Deixe o cliente clicar.** Você só narra. Ele precisa VIVER o "uau".
- **Mostre o admin primeiro só se pedirem.** Senão estraga a surpresa.
- **Se o cliente perguntar detalhe técnico no meio**, responda em 1 frase e siga o roteiro. Detalhe vai pro "tempos técnicos" depois.
- **Sempre termine com a frase de fechamento.** Ela amarra tudo.

---

## Versão "rápida" (90 segundos, pra call fria)

Se o cliente tem pouco tempo:

1. "Abre aqui, finge que é cliente." (30s pra extração multi-campo)
2. "Olha o CRM — preencheu sozinho." (10s)
3. "Custo: R$ 0,0X por conversa." (10s)
4. "Isso é o motor que entra no seu WhatsApp." (10s)
5. "Posso te mandar a proposta?" (10s)

Fim.
