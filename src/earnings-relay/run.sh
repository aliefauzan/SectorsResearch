#!/usr/bin/env bash
#
# Earnings Relay — satu laporan kuartalan masuk, satu paket konten siap tinjau keluar,
# dan setiap angka membawa endpoint, field, formula dan as_of-nya.
#
#   ./run.sh                       start everything: mock API, then the UI. Ctrl-C stops both.
#   ./run.sh poll                  one scheduler tick, on the terminal
#   ./run.sh poll --watch --every 30   the unattended loop, in process
#   ./run.sh runs                  every tick, and the review queue
#   ./run.sh draft 1               the draft, with the evidence behind every figure
#   ./run.sh review 1 --decision approve --as compliance
#   ./run.sh audit <event_id>      the append-only trail for one report event
#   ./run.sh symbols               what can be read, and which comparator is computable
#   ./run.sh demo                  the scripted five-run proof (AT-10)
#   ./run.sh test                  every gate — this product's, then the harness's
#   ./run.sh help
#
# SOURCE=recorded|synth picks the data layer. PORT (8082) and MOCK_PORT (8787) move the
# ports. State lives in state/relay.db; delete it to start the demo from nothing.
#
# Every command here is free. `adapter.py` refuses any base URL that is not localhost, so
# this folder cannot reach the paid API at all, and `test` runs the credit-ledger check.
#
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
HARNESS="$ROOT/research/harness"
PORT="${PORT:-8082}"
MOCK_PORT="${MOCK_PORT:-8787}"
SOURCE="${SOURCE:-recorded}"

command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 127; }

mock_is_up() {
  curl -sf -o /dev/null -m 2 -H "Authorization: dev-key" \
    "http://127.0.0.1:$MOCK_PORT/v2/subsectors/" 2>/dev/null
}

case "${1:-all}" in

  all)
    # The mock goes to the background so `--mode http` works from the CLI while the UI is
    # up. An already-running mock is reused rather than fought with over the port.
    mock_pid=""
    # mktemp, not a fixed path: a predictable name in a world-writable directory is a
    # redirect-to-arbitrary-file sink if somebody plants a symlink there first.
    MOCK_LOG="$(mktemp -t er-mock)"
    if mock_is_up; then
      echo "mock API   ·  sudah jalan di :$MOCK_PORT — dipakai ulang"
    else
      python3 "$HARNESS/src/mock_server.py" --port "$MOCK_PORT" --credits 1000 \
        >"$MOCK_LOG" 2>&1 &
      mock_pid=$!
      for _ in $(seq 1 40); do mock_is_up && break; sleep 0.25; done
      if mock_is_up; then
        echo "mock API   ·  http://127.0.0.1:$MOCK_PORT   (log: $MOCK_LOG)"
      else
        echo "mock API   ·  gagal start, lihat $MOCK_LOG — UI tetap jalan di atas" >&2
        echo "              rekaman; hanya --mode http yang membutuhkannya." >&2
      fi
    fi

    echo "relay      ·  http://127.0.0.1:$PORT        (sumber: $SOURCE, nol kredit)"
    echo "              Ctrl-C untuk berhenti."

    # The UI runs in the background and this script `wait`s on it. Bash defers a trap
    # while blocked on a foreground child, so the foreground form only cleans up when the
    # signal reaches the whole process group — true for a terminal Ctrl-C, not for
    # `kill <pid of run.sh>`, which would leave the mock running with nothing in front.
    python3 "$DIR/webapp.py" --port "$PORT" --source "$SOURCE" &
    ui_pid=$!

    # Only what this invocation started: a mock that was already up belongs to somebody
    # else, and running this twice must not take theirs down.
    cleanup() {
      trap - EXIT INT TERM
      kill "$ui_pid" 2>/dev/null || true
      if [ -n "$mock_pid" ]; then
        echo; echo "menghentikan mock ($mock_pid)"
        kill "$mock_pid" 2>/dev/null || true
      fi
    }
    trap cleanup EXIT INT TERM

    wait "$ui_pid" || true
    ;;

  ui)
    echo "relay      ·  http://127.0.0.1:$PORT   (tanpa mock; --mode http tidak tersedia)"
    exec python3 "$DIR/webapp.py" --port "$PORT" --source "$SOURCE"
    ;;

  mock)
    cd "$HARNESS"
    echo "mock API   ·  http://127.0.0.1:$MOCK_PORT"
    exec python3 src/mock_server.py --port "$MOCK_PORT" --credits 1000
    ;;

  poll|runs|draft|review|edit|audit|demo|setup|symbols)
    command="$1"; shift
    exec python3 "$DIR/relay.py" "$command" "$@" --source "$SOURCE"
    ;;

  test)
    # This product's gates first, then the harness's, so a failure here is attributable
    # to this folder rather than to the data layer underneath it.
    status=0
    for gate in sources periods money metrics factset store template gate; do
      echo "── $gate"
      python3 "$DIR/$gate.py" || status=1
    done
    echo "── adapter"
    python3 "$DIR/adapter.py" --self-test || status=1
    echo "── relay (AT-01 … AT-10)"
    python3 "$DIR/relay.py" --self-test || status=1
    echo "── webapp"
    python3 "$DIR/webapp.py" --self-test || status=1
    echo "── harness: mock vs captured API"
    (cd "$HARNESS" && python3 src/verify_mock.py >/dev/null) || status=1
    echo "── harness: credit ledger vs portal usage log"
    (cd "$HARNESS" && python3 src/reconcile_usage.py >/dev/null) || status=1
    if [ "$status" -eq 0 ]; then
      echo
      echo "semua gate lulus · nol kredit terpakai"
    else
      echo
      echo "ada gate yang gagal" >&2
    fi
    exit "$status"
    ;;

  help|-h|--help)
    sed -n '2,23p' "$0" | sed 's/^#\s\{0,1\}//'
    ;;

  *)
    echo "perintah tidak dikenal: $1" >&2
    sed -n '2,23p' "$0" | sed 's/^#\s\{0,1\}//' >&2
    exit 64
    ;;
esac
