#!/usr/bin/env bash
# Stop: impede encerrar o turno com a suite enfraquecida.
set -uo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$ROOT" || exit 0

DIFF="$(git diff HEAD -- '*.py' '*.ts' '*.tsx' 2>/dev/null || true)"
[ -z "$DIFF" ] && exit 0

FLAG=""
echo "$DIFF" | grep -E '^\+.*(pytest\.mark\.(skip|xfail)|@skip|it\.skip|test\.skip|describe\.skip|\.only\()' -q \
  && FLAG="foi adicionado skip/xfail/only em teste"
echo "$DIFF" | grep -E '^-.*(assert |expect\()' -q \
  && FLAG="${FLAG:+$FLAG; }uma assercao foi removida"

if [ -n "$FLAG" ]; then
  echo "INTEGRIDADE DE TESTES: $FLAG. Explique no relatorio por que, ou reverta antes de encerrar." >&2
  exit 2
fi
exit 0
