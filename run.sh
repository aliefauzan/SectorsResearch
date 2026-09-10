#!/usr/bin/env bash
#
# One entry point, so nobody has to remember which directory a script wants to be run
# from. Every command below is free: the default data source is the local recordings in
# research/harness/, and the live API is not reachable from here at all.
#
#   ./run.sh ui                      the browser UI on http://127.0.0.1:8080
#   ./run.sh score ADRO 2026-08-31   one symbol, one date, on the terminal
#   ./run.sh mock                    the offline API on :8787, for `--source mock`
#   ./run.sh eval                    precision and recall against the labels
#   ./run.sh test                    every gate, including the harness's own
#   ./run.sh symbols                 what can actually be scored, and when it flagged
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCT="$ROOT/firewall"
HARNESS="$ROOT/research/harness"
PORT="${PORT:-8080}"
MOCK_PORT="${MOCK_PORT:-8787}"

have_python() {
  command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 127; }
}

case "${1:-help}" in

  ui)
    have_python
    echo "firewall UI  →  http://127.0.0.1:$PORT     (recordings only, spends nothing)"
    exec python3 "$PRODUCT/webapp.py" --port "$PORT"
    ;;

  score)
    have_python
    symbol="${2:-ADRO}"
    # The date is optional: with none, firewall.py scores the most recent row it holds.
    if [ -n "${3:-}" ]; then
      exec python3 "$PRODUCT/firewall.py" "$symbol" --source "${SOURCE:-recorded}" --date "$3"
    else
      exec python3 "$PRODUCT/firewall.py" "$symbol" --source "${SOURCE:-recorded}"
    fi
    ;;

  mock)
    have_python
    cd "$HARNESS"
    echo "mock API →  http://127.0.0.1:$MOCK_PORT     then pick 'mock' in the UI dropdown"
    exec python3 src/mock_server.py --port "$MOCK_PORT" --credits 1000
    ;;

  eval)
    have_python
    exec python3 "$PRODUCT/eval_fragility.py" --source "${SOURCE:-synth}"
    ;;

  symbols)
    have_python
    # Reads the same universe the UI picker is built from, so what it prints is exactly
    # what can be selected — this is the check that stops another BNBR.
    exec python3 - "$PRODUCT" "${SOURCE:-recorded}" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import webapp
for s in webapp.available(sys.argv[2]):
    flags = ", ".join(s["flags"]) or "none"
    print(f'{s["symbol"]:6} {s["dates"][0]}..{s["dates"][-1]}  '
          f'broker={"yes" if s["broker"] else "no "}  flagged: {flags}')
PY
    ;;

  test)
    have_python
    failed=0
    # The product's own gates, then the harness gates that prove nothing was spent and
    # that the mock still matches the API we captured.
    run() {
      local label="$1"; shift
      if "$@" >/tmp/firewall-gate.out 2>&1; then
        printf 'PASS  %s\n' "$label"
      else
        printf 'FAIL  %s\n' "$label"; sed 's/^/        /' /tmp/firewall-gate.out; failed=1
      fi
    }
    run "fragility  scorer"        python3 "$PRODUCT/fragility.py"
    run "sources    shape parity"  python3 "$PRODUCT/sources.py"
    run "firewall   fail-closed"   python3 "$PRODUCT/firewall.py" --self-test
    run "webapp     api contract"  python3 "$PRODUCT/webapp.py" --self-test
    run "eval       synth"         python3 "$PRODUCT/eval_fragility.py" --source synth
    run "mock       API parity"    python3 "$HARNESS/src/verify_mock.py"
    run "credits    ledger vs portal" python3 "$HARNESS/src/reconcile_usage.py"
    echo
    if [ "$failed" -eq 0 ]; then
      echo "all gates pass — and the credit ledger is unchanged, so this cost nothing"
    else
      echo "at least one gate failed"
    fi
    exit "$failed"
    ;;

  help|-h|--help)
    # Stops at the first line that is not a comment, so the help text cannot drift out
    # of sync with the header above the way a hardcoded line range does.
    awk 'NR<3{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"
    ;;

  *)
    echo "unknown command: $1" >&2
    echo "try: ./run.sh help" >&2
    exit 2
    ;;
esac
