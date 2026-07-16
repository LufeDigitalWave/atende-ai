# Skill: Memory Management — Atende AI

## Quando usar

Use esta skill ao **final de cada sessão de trabalho** ou quando:
- Uma decisão arquitetural foi tomada
- Um deploy foi feito
- Um bug significativo foi encontrado/corrigido
- O estado do projeto mudou (novo nicho, nova feature, novo fix)
- O usuário pedir "salve na memória"

## O que manter atualizado

### 1. Memória do Claude Code (`~/.claude/projects/.../memory/`)

O arquivo principal é `project_atende_ai.md`. Deve conter:

- **Estado atual:** repo, VPS, domínio, último deploy
- **Stack:** tecnologias, providers, modelos
- **Arquitetura:** as 3 camadas (Factory → Renderer → Runtime)
- **Decisões-chave:** cada decisão com data e motivo
- **Testes:** quantos passam, quais nichos foram validados E2E
- **Arquivos principais:** mapa da estrutura relevante
- **Pendências:** o que falta fazer (priorizado)
- **Rate limits:** valores atuais de guardrails

### 2. CLAUDE.md (na raiz do repo)

Convenções do projeto. Atualizar quando:
- Filosofia ou princípios mudarem
- Arquitetura mudar (nova camada, novo fluxo)
- Estrutura de pastas mudar
- Novos arquivos importantes forem criados
- Convenções de código mudarem

### 3. MEMORY.md (índice de memórias)

Linha única por projeto. Formato:
```
- [Atende AI — ...](project_atende_ai.md) — resumo em 1 linha com estado atual
```

## Checklist de final de sessão

```markdown
- [ ] `project_atende_ai.md` reflete o estado real (deploy, commits, decisões)
- [ ] `CLAUDE.md` do repo está atualizado
- [ ] `MEMORY.md` tem a descrição correta do projeto
- [ ] Último commit está pushed no GitHub
- [ ] VPS está deployada com a versão mais recente (se houve mudança)
- [ ] Pendências estão listadas (para a próxima sessão saber o que fazer)
```

## Formato de atualização

Quando atualizar `project_atende_ai.md`:

1. **Não reescreva tudo** — edite cirurgicamente a seção relevante
2. **Datas absolutas** — nunca "ontem" ou "hoje"; use 2026-07-16
3. **Commits com hash** — ex: `1d0ac4c` pra referência futura
4. **Decisões com "Why"** — não só O QUE, mas POR QUE
5. **Links entre memórias** — use `[[nome-do-arquivo]]` pra referências cruzadas

## Exemplo de atualização pós-sessão

```markdown
## Sessão 16/07/2026 — Evolução v3

- Implementou ConversationProfile + scoring contextual
- Testou 30 nichos E2E (29/30 OK)
- CRM agora é dinâmico por nicho
- Commit: `1d0ac4c`
- Deploy: 23:22 UTC
- Pendência nova: diferenciar pet_name vs customer_name
```

## Anti-patterns

- ❌ Não salve código na memória (o repo já tem)
- ❌ Não salve secrets (senhas, keys)
- ❌ Não duplique informação que está no CLAUDE.md
- ❌ Não crie memórias separadas pra cada commit (1 arquivo por projeto basta)
- ❌ Não esqueça de atualizar o MEMORY.md quando mudar o project_atende_ai.md
