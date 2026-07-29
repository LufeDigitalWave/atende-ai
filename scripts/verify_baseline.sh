#!/usr/bin/env bash
# Compares current test counts against the baseline.
# Fails if passed count drops or skip/xfail count rises.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASELINE="$ROOT/.claude/baseline.json"

if [ ! -f "$BASELINE" ]; then
  echo "ERROR: baseline not found at $BASELINE"
  exit 1
fi

# Run backend
echo "=== Backend pytest ==="
BACKEND_OUT=$(cd "$ROOT/backend" && python -m pytest app/tests -q --tb=no 2>&1 | tail -1)
echo "$BACKEND_OUT"

# Extract numbers from pytest summary line like "115 passed, 9 xfailed, 4 warnings in 10.83s"
BE_PASSED=$(echo "$BACKEND_OUT" | grep -oP '\d+(?= passed)' || echo 0)
BE_XFAIL=$(echo "$BACKEND_OUT" | grep -oP '\d+(?= xfailed)' || echo 0)
BE_FAILED=$(echo "$BACKEND_OUT" | grep -oP '\d+(?= failed)' || echo 0)

# Run frontend unit
echo "=== Frontend vitest ==="
FE_OUT=$(cd "$ROOT/frontend" && npm test 2>&1 | grep -E 'Tests\s+' | tail -1)
echo "$FE_OUT"
FE_PASSED=$(echo "$FE_OUT" | grep -oP '\d+(?= passed)' || echo 0)

# Run E2E
echo "=== Frontend E2E ==="
E2E_OUT=$(cd "$ROOT/frontend" && npm run test:e2e 2>&1 | grep -E '^\s+\d+ passed' | tail -1)
echo "$E2E_OUT"
E2E_PASSED=$(echo "$E2E_OUT" | grep -oP '\d+(?= passed)' || echo 0)

# Read baseline
BL_BE_PASSED=$(python3 -c "import json;print(json.load(open('$BASELINE'))['suites']['backend_pytest']['passed'])")
BL_BE_XFAIL=$(python3 -c "import json;print(json.load(open('$BASELINE'))['suites']['backend_pytest']['xfailed'])")
BL_FE_PASSED=$(python3 -c "import json;print(json.load(open('$BASELINE'))['suites']['frontend_vitest']['passed'])")
BL_E2E_PASSED=$(python3 -c "import json;print(json.load(open('$BASELINE'))['suites']['frontend_e2e_playwright']['passed'])")

# Compare
FAIL=0

check_ge() {
  local name="$1" current="$2" baseline="$3"
  if [ "$current" -lt "$baseline" ]; then
    echo "FAIL: $name dropped from $baseline to $current"
    FAIL=1
  else
    echo "OK: $name $current (>= baseline $baseline)"
  fi
}

check_le() {
  local name="$1" current="$2" baseline="$3"
  if [ "$current" -gt "$baseline" ]; then
    echo "FAIL: $name rose from $baseline to $current"
    FAIL=1
  else
    echo "OK: $name $current (<= baseline $baseline)"
  fi
}

echo ""
echo "=== Baseline comparison ==="
check_ge "backend_passed" "$BE_PASSED" "$BL_BE_PASSED"
check_le "backend_xfailed" "$BE_XFAIL" "$BL_BE_XFAIL"
check_ge "frontend_passed" "$FE_PASSED" "$BL_FE_PASSED"
check_ge "e2e_passed" "$E2E_PASSED" "$BL_E2E_PASSED"

if [ "$BE_FAILED" -gt 0 ]; then
  echo "FAIL: backend has $BE_FAILED test failures"
  FAIL=1
fi

if [ $FAIL -ne 0 ]; then
  echo ""
  echo "BASELINE CHECK FAILED — fix before merging."
  exit 1
fi

echo ""
echo "BASELINE CHECK PASSED"
exit 0
