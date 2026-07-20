# Contributing

Obrigado pelo interesse em contribuir com o Atende AI!

## Setup rápido

```bash
# Clonar e entrar
git clone https://github.com/<ORG>/atende-ai.git
cd atende-ai

# Backend
cd backend
uv sync            # ou pip install -e ".[dev]"
pytest -q          # 145+ testes devem passar
ruff check .       # lint

# Frontend
cd ../frontend
npm install
npm run build      # deve compilar sem erros
npm test           # vitest
```

## Convenções de commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat(scope):` — nova funcionalidade
- `fix(scope):` — correção de bug
- `docs:` — documentação
- `chore:` — manutenção (deps, CI, config)
- `refactor:` — mudança sem alterar comportamento
- `test:` — adição/correção de testes

## Pull Requests

1. Crie uma branch a partir de `main`: `feat/minha-feature`.
2. Faça commits atômicos seguindo a convenção acima.
3. Descreva brevemente o que testou (manual ou automatizado).
4. Garanta que `pytest` e `npm run build` passam antes de abrir PR.

## Regras detalhadas

Veja [`CLAUDE.md`](CLAUDE.md) para regras de arquitetura, estilo e comportamento do projeto.

## Licença

Ao contribuir, você concorda que sua contribuição será licenciada sob a [MIT License](LICENSE).
