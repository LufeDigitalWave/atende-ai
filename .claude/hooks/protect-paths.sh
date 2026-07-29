#!/usr/bin/env bash
# PreToolUse: bloqueia escrita em caminhos protegidos e comandos de risco.
# exit 2 = BLOQUEIA e devolve o stderr ao modelo. exit 0 = permite.
# exit 1 NAO bloqueia nada — nunca use 1 aqui.
set -uo pipefail

INPUT="$(cat)"
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

read_field() {
  printf '%s' "$INPUT" | python3 -c \
    "import sys,json;d=json.load(sys.stdin);print(d.get('tool_input',{}).get('$1','') or '')" \
    2>/dev/null || true
}

FILE_PATH="$(read_field file_path)"
COMMAND="$(read_field command)"

deny() { echo "BLOQUEADO PELO HARNESS: $1" >&2; exit 2; }

# 1) Caminhos protegidos (globs, um por linha, em .claude/protected-paths.txt)
if [ -n "$FILE_PATH" ] && [ -f "$ROOT/.claude/protected-paths.txt" ]; then
  REL="${FILE_PATH#$ROOT/}"
  while IFS= read -r pattern; do
    [ -z "$pattern" ] && continue
    case "$pattern" in \#*) continue ;; esac
    # shellcheck disable=SC2254
    case "$REL" in
      $pattern) deny "'$REL' esta protegido. Peca autorizacao explicita ao Luiz e explique por que a mudanca e necessaria. Nao contorne." ;;
    esac
  done < "$ROOT/.claude/protected-paths.txt"
fi

# 2) Comandos de risco no Bash
if [ -n "$COMMAND" ]; then
  case "$COMMAND" in
    *".claude/"*|*"protected-paths"*)
      deny "Comando toca em .claude/. O harness nao se edita a si mesmo." ;;
    *"rm -rf"*|*"git checkout -- "*|*"git reset --hard"*|*"git clean -fd"*)
      deny "Comando destrutivo. Se e realmente necessario, peca autorizacao." ;;
    *"--no-verify"*|*"-p no:cacheprovider"*|*"--exitfirst --no-header -q"*)
      deny "Tentativa de contornar verificacao. Corrija a causa, nao o sintoma." ;;
    *"pytest"*"--deselect"*|*"pytest"*"-k not "*)
      deny "Selecao de testes que exclui casos. Rode a suite inteira." ;;
  esac
fi

exit 0
