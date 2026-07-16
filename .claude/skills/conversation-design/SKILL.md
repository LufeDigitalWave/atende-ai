# Skill: Conversation Design

Use esta skill quando o trabalho envolver:

- Criar ou modificar jornadas de conversa.
- Ajustar `ConversationProfile` (intents, journeys, qualification_fields,
  prohibited_behaviors, handoff_rules).
- Melhorar naturalidade do agente.
- Adicionar novo nicho.
- Revisar tom, quantidade de perguntas, proatividade.
- Corrigir bug de "agente perguntou coisa errada".

---

## Princípios obrigatórios

1. **Responda antes de qualificar** — o visitante fez pergunta? Responda.
   Depois (se quiser) colete 1 dado.
2. **1 pergunta por mensagem** — nunca 2+.
3. **Mensagem curta** — 1-3 frases. WhatsApp, não email.
4. **Sem alucinação** — não invente preço, resultado, certificação.
5. **Sem orçamento em transacional** — restaurante, delivery, horário
   = zero `budget_range`.
6. **Handoff imediato** se pediu humano — sem re-qualificar.
7. **Emojis opcionais** — máximo 1 por msg.

## Onde editar

| O que mudar | Arquivo |
|---|---|
| Regras de comportamento do agente | `backend/app/agent/prompts/agent_template_v3.md` |
| Dados gerados por nicho | `backend/app/agent/prompts/factory_v3.md` |
| Schema do perfil de conversa | `backend/app/schemas/conversation_profile.py` |
| Fallback (Sofia/Clínica Renova) | `backend/app/services/prompt_factory_v3.py:_fallback_conversation()` |
| Jornadas de teste | `docs/EVALUATION.md` seção 2 |

## Checklist ao alterar jornada

- [ ] Adicionou/atualizou `ConversationJourney` no schema?
- [ ] `qualification_fields` do journey só contêm campos que existem em
  `ConversationProfile.qualification_fields`?
- [ ] `handoff_conditions` são concretas e verificáveis?
- [ ] `forbidden_questions` impedem perguntas inapropriadas pro nicho?
- [ ] Teste manual: 3 conversas no `LLM_PROVIDER=fake`, verifica que CRM
  atualiza.
- [ ] `pytest tests/test_prompt_renderer_v3.py tests/test_conversation_profile.py` verde.
- [ ] Documentar em `docs/AGENT_PROMPT.md` (changelog).

## Checklist ao adicionar nicho

- [ ] Definiu `business_mode` (reservation_based, appointment_based,
  consultative, transactional, mixed)?
- [ ] Listou 3-6 `primary_intents` realistas?
- [ ] Criou ≥1 `ConversationJourney` com campos, handoff e proibições?
- [ ] `qualification_fields` tem 2-6 campos úteis com `purpose`?
- [ ] `lead_scoring_rules` reflete importância real dos campos?
- [ ] `proactive_opening_strategy` evita "como posso ajudar?"?
- [ ] Adicionou cenários de teste em `docs/EVALUATION.md`?
- [ ] Testou extração com `test_lead_extractor.py` (novo fixture)?

## Anti-patterns a evitar

- **Formulário disfarçado:** lista longa de campos obrigatórios.
- **Qualificação precoce:** pedir nome/telefone antes de ajudar.
- **Orçamento universal:** não existe nicho onde orçamento é SEMPRE a
  primeira pergunta.
- **Quick reply como muleta:** quick replies complementam, não substituem
  texto natural.
- **"Posso te ajudar com mais alguma coisa?"** — genérico demais; prefira
  próximo passo concreto.
- **Template condicional:** se sentiu vontade de colocar if/else no
  template, pare — dados do ConversationProfile devem resolver.

## Referência rápida

- Doc completo: `docs/CONVERSATION_DESIGN.md`
- ADR: `docs/adr/ADR-001-conversation-profile.md`
- Rubrica: `docs/EVALUATION.md` seção 3
- Cenários: `docs/EVALUATION.md` seção 2
