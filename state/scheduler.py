#!/usr/bin/env python3
"""Scheduler harian earnings-relay — bukti unattended run (Track 02).

Menjalankan gate produk dan runner serangan terhadap data terekam / mock server,
lalu menulis hasilnya ke state/runs/ dan state/scheduler.jsonl (append-only).

Nol kredit Sectors: SECTORS_BASE_URL menunjuk mock, sumber data recorded/.
Dijalankan oleh cron; lihat state/schedule_config.md.
"""
import datetime
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RELAY = ROOT / "src" / "earnings-relay"
STATE = ROOT / "state"
RUN_DIR = STATE / "runs"
LOG = STATE / "scheduler.jsonl"

BASE_URL = os.environ.get("SECTORS_BASE_URL", "http://127.0.0.1:8787")


def run(cmd):
    """Jalankan satu perintah, kembalikan (exit_code, stdout+stderr)."""
    proc = subprocess.run(
        cmd, cwd=RELAY, capture_output=True, text=True,
        env={**os.environ, "SECTORS_BASE_URL": BASE_URL},
    )
    return proc.returncode, (proc.stdout + proc.stderr)


def main():
    started = datetime.datetime.now().astimezone()
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    gate_code, gate_out = run([sys.executable, "gate.py"])
    attack_code, attack_out = run([sys.executable, "attack_classes.py", "--run"])

    passes = sum(1 for line in gate_out.splitlines() if line.startswith("PASS"))
    fails = sum(1 for line in gate_out.splitlines() if line.startswith("FAIL"))
    catch = next(
        (line.strip() for line in attack_out.splitlines() if "CATCH RATE" in line),
        "catch rate tidak terbaca",
    )
    finished = datetime.datetime.now().astimezone()

    entry = {
        "run_id": started.strftime("%Y-%m-%dT%H%M%S%z"),
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_s": round((finished - started).total_seconds(), 2),
        "base_url": BASE_URL,
        "gate_exit": gate_code,
        "gate_pass": passes,
        "gate_fail": fails,
        "catch_rate": catch,
        "status": "ok" if gate_code == 0 and attack_code == 0 else "fail",
        "credits_spent": 0,
    }

    (RUN_DIR / f"{entry['run_id']}.json").write_text(json.dumps(entry, indent=2) + "\n")
    with LOG.open("a") as handle:
        handle.write(json.dumps(entry) + "\n")

    print(f"{entry['status']} · {entry['started_at']} · gate {passes} PASS / {fails} FAIL · {catch}")
    return 0 if entry["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
