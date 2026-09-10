#!/usr/bin/env bash
#
# Firewall Tip Saham — one IDX symbol in, a fragility verdict out, every number carrying
# the (endpoint, field) it came from.
#
#   run.sh ui                      the browser UI on http://127.0.0.1:8080
#   run.sh score ADRO 2026-08-31   one symbol, one date, on the terminal
#   run.sh symbols                 what can actually be scored, and when it flagged
#   run.sh eval                    precision and recall against the labels
#   run.sh test                    this idea's gates
#
# SOURCE=recorded|synth|mock picks the data layer (default: recorded). PORT moves the UI.
# Every command here is free — nothing in this folder can reach the live API without
# firewall.py's --i-mean-it and an explicit --budget.
#
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-8080}"

command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 127; }

case "${1:-help}" in

  ui)
    echo "pump-and-dump UI  →  http://127.0.0.1:$PORT     (recordings only, spends nothing)"
    exec python3 "$DIR/webapp.py" --port "$PORT"
    ;;

  score)
    # The date is optional: with none, firewall.py scores the most recent row it holds.
    if [ -n "${3:-}" ]; then
      exec python3 "$DIR/firewall.py" "${2:-ADRO}" --source "${SOURCE:-recorded}" --date "$3"
    else
      exec python3 "$DIR/firewall.py" "${2:-ADRO}" --source "${SOURCE:-recorded}"
    fi
    ;;

  symbols)
    # The same universe the UI picker is built from, so what it prints is exactly what can
    # be selected — this is the check that stops another BNBR.
    exec python3 - "$DIR" "${SOURCE:-recorded}" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import webapp
for s in webapp.available(sys.argv[2]):
    flags = ", ".join(s["flags"]) or "none"
    print(f'{s["symbol"]:6} {s["dates"][0]}..{s["dates"][-1]}  '
          f'broker={"yes" if s["broker"] else "no "}  flagged: {flags}')
PY
    ;;

  eval)
    exec python3 "$DIR/eval_fragility.py" --source "${SOURCE:-synth}"
    ;;

  test)
    failed=0
    run() {
      local label="$1"; shift
      if "$@" >/tmp/pnd-gate.out 2>&1; then
        printf 'PASS  %s\n' "$label"
      else
        printf 'FAIL  %s\n' "$label"; sed 's/^/        /' /tmp/pnd-gate.out; failed=1
      fi
    }
    run "fragility  scorer"       python3 "$DIR/fragility.py"
    run "sources    shape parity" python3 "$DIR/sources.py"
    run "firewall   fail-closed"  python3 "$DIR/firewall.py" --self-test
    run "webapp     api contract" python3 "$DIR/webapp.py" --self-test
    run "eval       on synth"     python3 "$DIR/eval_fragility.py" --source synth
    exit "$failed"
    ;;

  help|-h|--help)
    awk 'NR<3{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"
    ;;

  *)
    echo "unknown command: $1" >&2
    echo "try: $0 help" >&2
    exit 2
    ;;
esac
