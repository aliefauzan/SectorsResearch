#!/usr/bin/env bash
#
# The router. Each idea in src/ owns its own run.sh and its own vocabulary — this file
# only decides which one you meant, and holds the two things no single idea owns.
#
# Ideas are named after the research folder they came from, so src/pump-and-dump/ answers
# to research/plan/pump-and-dump/ and the next one pairs off the same way.
#
#   src/run.sh ideas                          what exists, and what each one answers to
#   src/run.sh <idea> <command> [args...]     hand the command to that idea
#   src/run.sh <command> [args...]            same, for the default idea
#   src/run.sh mock                           the offline API on :8787 — shared
#   src/run.sh test                           every idea's gates, then the harness's
#
# IDEA=<name> changes the default. Commands other than `ideas`, `mock` and `test` belong
# to the idea, not to this file, so ask it what it takes:
#
#   src/run.sh pump-and-dump help
#
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SRC")"
HARNESS="$ROOT/research/harness"
IDEA="${IDEA:-pump-and-dump}"
MOCK_PORT="${MOCK_PORT:-8787}"

command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 127; }

ideas() {
  find "$SRC" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort
}

delegate() {
  local idea="$1"; shift
  local script="$SRC/$idea/run.sh"
  if [ ! -x "$script" ]; then
    if [ -d "$SRC/$idea" ]; then
      echo "idea '$idea' has no executable run.sh yet" >&2
    else
      echo "no such idea: $idea" >&2
      echo "available: $(ideas | tr '\n' ' ')" >&2
    fi
    exit 2
  fi
  exec "$script" "$@"
}

case "${1:-help}" in

  ideas)
    for name in $(ideas); do
      # Every idea answers `help`; its first line of help is its own description, so this
      # listing cannot go stale the way a table maintained here would.
      if [ -x "$SRC/$name/run.sh" ]; then
        printf '%-16s %s\n' "$name" "$("$SRC/$name/run.sh" help 2>/dev/null | head -1)"
      else
        printf '%-16s %s\n' "$name" "(no run.sh yet)"
      fi
    done
    ;;

  mock)
    # Shared: the mock serves the recordings every idea reads, so it belongs to none of them.
    cd "$HARNESS"
    echo "mock API →  http://127.0.0.1:$MOCK_PORT     then pick 'mock' in the UI dropdown"
    exec python3 src/mock_server.py --port "$MOCK_PORT" --credits 1000
    ;;

  test)
    failed=0
    for name in $(ideas); do
      [ -x "$SRC/$name/run.sh" ] || continue
      grep -q '^  test)' "$SRC/$name/run.sh" || continue
      echo "── $name"
      "$SRC/$name/run.sh" test || failed=1
    done
    echo "── harness"
    # The credit ledger is the gate that matters: a run that leaked a credit fails the
    # suite here, rather than being noticed a week later in the portal export.
    for gate in verify_mock reconcile_usage; do
      if python3 "$HARNESS/src/$gate.py" >/tmp/run-gate.out 2>&1; then
        printf 'PASS  %s\n' "$gate"
      else
        printf 'FAIL  %s\n' "$gate"; sed 's/^/        /' /tmp/run-gate.out; failed=1
      fi
    done
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
    # An idea name routes to that idea; anything else is a command for the default one.
    if [ -d "$SRC/$1" ]; then
      name="$1"; shift
      delegate "$name" "$@"
    fi
    delegate "$IDEA" "$@"
    ;;
esac
