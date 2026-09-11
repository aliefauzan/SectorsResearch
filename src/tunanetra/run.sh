#!/usr/bin/env bash
#
# Riset fundamental IDX yang bisa didengar — one symbol in, sentences and semantic
# tables out, every number carrying the (endpoint, field, window) it came from.
#
#   ./run.sh                       start everything: the UI on the recordings. Ctrl-C stops it.
#   ./run.sh read BBCA             one symbol, on the terminal
#   ./run.sh read TLKM --lengkap   every section, not just the summary
#   ./run.sh symbols               what can be read, and the real window of every series
#   ./run.sh a11y                  the WCAG criteria this product actually claims
#   ./run.sh test                  every gate — this product's, then the harness's
#   ./run.sh help
#
# SOURCE=recorded|synth picks the data layer. PORT moves the port.
#
# Every command here is free. Nothing in this folder can reach the live API at all —
# there is no client in it — and `test` runs the credit-ledger check, so a run that
# somehow leaked a credit fails the suite instead of surfacing a week later.
#
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
HARNESS="$ROOT/research/harness"
PORT="${PORT:-8081}"
SOURCE="${SOURCE:-recorded}"

command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 127; }

case "${1:-all}" in

  all|ui)
    echo "riset saham ·  http://127.0.0.1:$PORT        (sumber: $SOURCE, nol kredit)"
    echo "               Ctrl-C untuk berhenti."
    exec python3 "$DIR/webapp.py" --port "$PORT" --source "$SOURCE"
    ;;

  read)
    shift
    exec python3 "$DIR/reader.py" read "$@" --source "$SOURCE"
    ;;

  symbols)
    exec python3 "$DIR/reader.py" symbols --source "$SOURCE"
    ;;

  a11y)
    exec python3 "$DIR/a11y_check.py"
    ;;

  test)
    # This product's gates first, then the harness's, so a failure here is attributable
    # to this folder rather than to the data layer underneath it.
    status=0
    for gate in sources money narrate; do
      echo "── $gate"
      python3 "$DIR/$gate.py" || status=1
    done
    echo "── reader"
    python3 "$DIR/reader.py" --self-test || status=1
    echo "── webapp"
    python3 "$DIR/webapp.py" --self-test || status=1
    echo "── accessibility"
    python3 "$DIR/a11y_check.py" || status=1
    python3 "$DIR/a11y_check.py" --broken >/dev/null || status=1
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
    sed -n '2,20p' "$0" | sed 's/^#\s\{0,1\}//'
    ;;

  *)
    echo "perintah tidak dikenal: $1" >&2
    sed -n '2,20p' "$0" | sed 's/^#\s\{0,1\}//' >&2
    exit 64
    ;;
esac
