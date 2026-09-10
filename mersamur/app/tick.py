#!/usr/bin/env python3
"""One daily cycle. Appends exactly one line to state/runs.jsonl, and sends the
transitions to Telegram.

    python3 app/tick.py --dry-run     # runs, prints the line and what would be sent
    python3 app/tick.py               # appends one line, sends the transitions

Zero credits: the cycle screens the watchlist over the payloads already cached in
research/harness/recorded/. The run history is the point — Track 02 asks for logs of
unattended runs across days, and three weeks of history cannot be produced on 29
September.

## What changed in task 19

The screen was `tools/profile_demo.py`, a prototype that answered "how many axes
lit" with its own simplified rules. It is now `app/profile.py` and
`app/render/paragraph.py` — the real axes, reading the bars out of
`state/thresholds.json`, and the paragraph with a citation behind every figure.

That swap changes the numbers in `runs.jsonl`, and it should: the prototype's looser
rules put seven of ten watchlist symbols past the bar, and the shipped bars put
none of them there. A quieter log that comes from the bars the product actually
documents is worth more than a busy one that comes from a placeholder.

The record's shape is unchanged. Delivery is reported inside `notes` rather than in
new fields, so a log read on 30 September parses the same way as the first line
written on 9 September.

## Delivery is a transition trigger, not a daily digest

`app/render/notify.py` holds the rule and the reasoning: a message goes out when a
symbol *enters* the lit-axes state, never while it sits there. Delivery failure is
recorded in the note and never raised — a Telegram outage must not put a hole in the
run history, least of all on a day something was worth saying.
"""
import argparse
import json
import os
import sys
import time
import uuid
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config, profile as profile_mod  # noqa: E402
from app.cache import Cache  # noqa: E402
from app.render import notify  # noqa: E402


def screen(cache=None):
    """Run the four axes over the watchlist against the bars in `thresholds.json`.

    Returns `(screened, lit, missing, notes)`, where `lit` maps symbol to `Profile`
    for everything at or past `config.WARNING_AXES_THRESHOLD`. A symbol with no
    measurable axis is not counted as screened — silently treating it as "no
    warning" would make an empty cache look like a calm market.
    """
    cache = cache or Cache()
    screened, lit, missing = 0, {}, []

    for symbol in config.WATCHLIST:
        try:
            profile = profile_mod.build(symbol, cache=cache)
        except Exception as exc:                 # one bad symbol, not a bad cycle
            missing.append(f"{symbol} ({type(exc).__name__})")
            continue
        if not any(reading.measured for reading in profile.counted):
            missing.append(profile.symbol)
            continue
        screened += 1
        if profile.axes_fired >= config.WARNING_AXES_THRESHOLD:
            lit[profile.symbol] = profile

    notes = f"{screened} simbol dibaca dari cache"
    if lit:
        notes += (f"; {len(lit)} melewati ambang {config.WARNING_AXES_THRESHOLD} "
                  f"sumbu: {', '.join(lit)}")
    else:
        notes += f"; tidak ada yang melewati ambang {config.WARNING_AXES_THRESHOLD} sumbu"
    if missing:
        notes += f"; tanpa data cache: {', '.join(missing)}"
    return screened, lit, missing, notes


def build_record(today=None, dry_run=False, cache=None):
    """Run one cycle, deliver its transitions, and return the record. Never raises."""
    today = today or date.today()
    cache = cache or Cache()
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
    outcome = None

    if not config.is_trading_day(today):
        reason = "akhir pekan" if today.weekday() >= 5 else "libur bursa IDX"
        record["notes"] = f"{reason} — siklus dilewati"
    else:
        try:
            screened, lit, _missing, notes = screen(cache=cache)
            record["symbols_screened"] = screened
            record["warnings_emitted"] = len(lit)
            record["notes"] = notes
        except Exception as exc:  # a broken cycle must still leave a trace
            record["status"] = "error"
            record["notes"] = f"{type(exc).__name__}: {exc}"
        else:
            # Delivery is its own try: a screen that worked is a screen that gets
            # logged, whatever Telegram does with the result.
            try:
                outcome = notify.deliver(lit, dry_run=dry_run, when=today,
                                         cache=cache)
                record["notes"] += "; " + outcome.note()
            except Exception as exc:
                record["notes"] += f"; pengiriman gagal ({type(exc).__name__}: {exc})"

    record["duration_ms"] = int((time.monotonic() - started) * 1000)
    return record, outcome


def append(record):
    os.makedirs(config.STATE_DIR, exist_ok=True)
    with open(config.RUNS_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Satu siklus harian pemeriksa kerapuhan.")
    ap.add_argument("--dry-run", action="store_true",
                    help="jalankan siklus, cetak barisnya dan pesan yang akan "
                         "dikirim, jangan tulis atau kirim apa pun")
    args = ap.parse_args(argv)

    record, outcome = build_record(dry_run=args.dry_run)
    line = json.dumps(record, ensure_ascii=False)

    if args.dry_run:
        print("[dry-run] tidak ada yang ditulis, tidak ada yang dikirim.")
        print(f"[dry-run] Telegram: "
              f"{'terkonfigurasi' if notify.configured() else 'belum diset'} "
              f"({notify.TOKEN_VAR}, {notify.CHAT_VAR})")
        print("[dry-run] Baris yang akan ditambahkan:")
        print(line)
        print("[dry-run] Pesan yang akan dikirim:")
        if outcome is None or not outcome.messages:
            reason = ("tidak ada transisi baru — hanya saham yang *memasuki* "
                      "keadaan sumbu menyala yang dikirim")
            for failure in (outcome.deliveries if outcome else []):
                reason = f"{failure.symbol}: {failure.detail}"
            print(f"  (tidak ada) {reason}")
        for message in (outcome.messages if outcome else []):
            print("  " + "-" * 70)
            for text_line in message.text.splitlines():
                print(f"  {text_line}")
        if outcome and outcome.leaving:
            print(f"[dry-run] keluar dari keadaan sumbu menyala: "
                  f"{', '.join(outcome.leaving)}")
    else:
        append(record)
        print(f"ditulis ke {os.path.relpath(config.RUNS_PATH, config.PKG_ROOT)}: {line}")

    # A cycle that errored still exits 0: the run happened and was recorded. The
    # scheduler must not stop, and the log is where failures are read.
    return 0


if __name__ == "__main__":
    sys.exit(main())
