#!/usr/bin/env bash
#
# Firewall Tip Saham — one IDX symbol in, a fragility verdict out, every number carrying
# the (endpoint, field) it came from.
#
#   ./run.sh                       start everything: mock API, then the UI. Ctrl-C stops both.
#   ./run.sh score ADRO 2026-08-31 one symbol, one date, on the terminal
#   ./run.sh symbols               what can actually be scored, and when it flagged
#   ./run.sh eval                  precision and recall against the labels
#   ./run.sh test                  every gate — this product's, and the harness's
#   ./run.sh ui                    the UI alone, without the mock behind it
#
# SOURCE=recorded|synth|mock picks the data layer for score and eval (default: recorded).
# PORT and MOCK_PORT move the ports.
#
# Every command here is free. Nothing in this folder reaches the live API without
# firewall.py's --i-mean-it and an explicit --budget, and `test` runs the credit ledger
# check, so a run that leaked a credit fails the suite instead of surfacing a week later.
#
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
HARNESS="$ROOT/research/harness"
PORT="${PORT:-8080}"
MOCK_PORT="${MOCK_PORT:-8787}"

command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 127; }

mock_is_up() {
  curl -sf -o /dev/null -m 2 -H "Authorization: dev-key" \
    "http://127.0.0.1:$MOCK_PORT/v2/subsectors/" 2>/dev/null
}

case "${1:-all}" in

  all)
    # The whole thing, from nothing. The mock goes to the background so the UI's third
    # source option actually works; without it, picking "mock" in the dropdown fails.
    # An already-running mock is reused rather than fought with over the port.
    mock_pid=""
    if mock_is_up; then
      echo "mock API   ·  already running on :$MOCK_PORT — reusing it"
    else
      python3 "$HARNESS/src/mock_server.py" --port "$MOCK_PORT" --credits 1000 \
        >/tmp/pnd-mock.log 2>&1 &
      mock_pid=$!
      for _ in $(seq 1 40); do mock_is_up && break; sleep 0.25; done
      if mock_is_up; then
        echo "mock API   ·  http://127.0.0.1:$MOCK_PORT   (log: /tmp/pnd-mock.log)"
      else
        echo "mock API   ·  failed to start, see /tmp/pnd-mock.log — the UI still works" >&2
        echo "              on 'recorded' and 'synth'; only the 'mock' option needs it." >&2
      fi
    fi

    echo "firewall   ·  http://127.0.0.1:$PORT        (recordings only, spends nothing)"
    echo "              Ctrl-C to stop."

    # The UI runs in the background and this script `wait`s on it, rather than running it
    # in the foreground. Bash defers a trap while it is blocked on a foreground child, so
    # the foreground form only cleans up when the signal reaches the whole process group —
    # true for a terminal Ctrl-C, but not for `kill <pid of run.sh>`, which would leave the
    # mock running with nothing in front of it. Waiting makes both paths behave the same.
    python3 "$DIR/webapp.py" --port "$PORT" &
    ui_pid=$!

    # Only what this invocation started: a mock that was already up belongs to somebody
    # else, and running this twice must not take theirs down.
    cleanup() {
      trap - EXIT INT TERM
      kill "$ui_pid" 2>/dev/null || true
      if [ -n "$mock_pid" ]; then
        echo; echo "stopping mock ($mock_pid)"
        kill "$mock_pid" 2>/dev/null || true
      fi
    }
    trap cleanup EXIT INT TERM

    wait "$ui_pid" || true
    ;;

  ui)
    echo "firewall   ·  http://127.0.0.1:$PORT   (no mock behind it — 'mock' source will fail)"
    exec python3 "$DIR/webapp.py" --port "$PORT"
    ;;

  mock)
    cd "$HARNESS"
    echo "mock API   ·  http://127.0.0.1:$MOCK_PORT"
    exec python3 src/mock_server.py --port "$MOCK_PORT" --credits 1000
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
    run "fragility  scorer"        python3 "$DIR/fragility.py"
    run "sources    shape parity"  python3 "$DIR/sources.py"
    run "firewall   fail-closed"   python3 "$DIR/firewall.py" --self-test
    run "webapp     api contract"  python3 "$DIR/webapp.py" --self-test
    run "eval       on synth"      python3 "$DIR/eval_fragility.py" --source synth
    run "harness    mock parity"   python3 "$HARNESS/src/verify_mock.py"
    run "harness    ledger vs portal" python3 "$HARNESS/src/reconcile_usage.py"
    echo
    if [ "$failed" -eq 0 ]; then
      echo "all gates pass — and the credit ledger is unchanged, so this cost nothing"
    else
      echo "at least one gate failed"
    fi
    exit "$failed"
    ;;

  help|-h|--help)
    awk 'NR<3{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"
    ;;

  *)
    echo "unknown command: $1" >&2
    echo "try: ./run.sh help" >&2
    exit 2
    ;;
esac
