#!/usr/bin/env python3
"""One daily cycle. Appends exactly one line to state/runs.jsonl.

    python3 app/tick.py --dry-run     # prints the line, writes nothing
    python3 app/tick.py               # appends one line

Zero credits: the cycle screens the watchlist over the payloads already cached in
research/harness/recorded/. The point of this file today is not its logic — it is
that the run history starts accumulating now, with real timestamps, because Track
02 asks for logs of unattended runs across days and three weeks of history cannot
be produced on 29 September.

The screening body is still deliberately thin; it will be replaced by the axes
modules in later tasks. The record it writes will not change shape.
"""
import argparse
import json
import os
import sys
import time
import uuid
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config  # noqa: E402

sys.path.insert(0, config.TOOLS_DIR)
import profile_demo  # noqa: E402  — the cached-data screening logic, for now


def screen():
    """Run the current (placeholder) screen over the watchlist.

    Returns (symbols_screened, warnings_emitted, notes). Symbols whose cached
    payloads are missing are not counted as screened — silently treating them as
    "no warning" would make an empty cache look like a clean market.
    """
    brokers = {b["code"]: b for b in (profile_demo.load("v2_brokers") or [])}
    susp = (profile_demo.load("v2_suspensions__limit-30") or {}).get("results") or []

    screened, warned, missing = 0, [], []
    for sym in config.WATCHLIST:
        out = profile_demo.profile(sym, brokers, susp)
        if out is None:
            missing.append(sym)
            continue
        screened += 1
        _lines, _cites, fired, _axes = out
        if fired >= config.WARNING_AXES_THRESHOLD:
            warned.append(sym)

    notes = f"{screened} simbol dibaca dari cache"
    if warned:
        notes += (f"; {len(warned)} melewati ambang {config.WARNING_AXES_THRESHOLD} "
                  f"sumbu: {', '.join(warned)}")
    else:
        notes += f"; tidak ada yang melewati ambang {config.WARNING_AXES_THRESHOLD} sumbu"
    if missing:
        notes += f"; tanpa data cache: {', '.join(missing)}"
    return screened, len(warned), notes


def build_record(today=None):
    """Run one cycle and return the record to append. Never raises."""
    today = today or date.today()
    started = time.monotonic()
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "run_id": f"{today.isoformat()}-{uuid.uuid4().hex[:8]}",
        "symbols_screened": 0,
        "warnings_emitted": 0,
        "duration_ms": 0,
        "status": "ok",
        "notes": "",
    }

    if not config.is_trading_day(today):
        reason = "akhir pekan" if today.weekday() >= 5 else "libur bursa IDX"
        record["notes"] = f"{reason} — siklus dilewati"
    else:
        try:
            screened, warned, notes = screen()
            record["symbols_screened"] = screened
            record["warnings_emitted"] = warned
            record["notes"] = notes
        except Exception as exc:  # a broken cycle must still leave a trace
            record["status"] = "error"
            record["notes"] = f"{type(exc).__name__}: {exc}"

    record["duration_ms"] = int((time.monotonic() - started) * 1000)
    return record


def append(record):
    os.makedirs(config.STATE_DIR, exist_ok=True)
    with open(config.RUNS_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Satu siklus harian pemeriksa kerapuhan.")
    ap.add_argument("--dry-run", action="store_true",
                    help="jalankan siklus, cetak barisnya, jangan tulis apa pun")
    args = ap.parse_args(argv)

    record = build_record()
    line = json.dumps(record, ensure_ascii=False)

    if args.dry_run:
        print("[dry-run] tidak ada yang ditulis. Baris yang akan ditambahkan:")
        print(line)
    else:
        append(record)
        print(f"ditulis ke {os.path.relpath(config.RUNS_PATH, config.PKG_ROOT)}: {line}")

    # A cycle that errored still exits 0: the run happened and was recorded. The
    # scheduler must not stop, and the log is where failures are read.
    return 0


if __name__ == "__main__":
    sys.exit(main())
