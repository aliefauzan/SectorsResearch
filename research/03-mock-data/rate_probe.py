#!/usr/bin/env python3
"""
Find the rate limit the documentation refuses to publish — without spending credits.

The trick is that a 400 is free. `/v2/index-daily/klse/` is a well-formed request for an
index code that does not exist, so it costs nothing and can be sent as fast as we like; if
the limiter sits in front of billing, it will still answer 429. Phase 0 tests exactly that
assumption before anything else runs, and the whole probe aborts if it turns out false.

    python3 rate_probe.py --phase0            # is the free path rate limited at all?
    python3 rate_probe.py                     # full sweep across spacings
    python3 rate_probe.py --confirm 0.5       # spend a few credits confirming one spacing

Every request is logged to recorded/_rate_probe.jsonl with its wall-clock offset, so the
shape of the limit (per-second burst, per-minute window, token bucket) can be read off
afterwards rather than guessed.
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request

from sectors_env import api_key, base_url

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "recorded", "_rate_probe.jsonl")

FREE_PATH = "/v2/index-daily/klse/"      # 400, free — an index code that does not exist
BILLED_PATH = "/v2/subsectors/"          # 200, 1 credit — only used by --confirm

USER_AGENT = os.environ.get(
    "SECTORS_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)


def log(entry):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as fh:
        fh.write(json.dumps(entry) + "\n")


def hit(path, key, base):
    started = time.time()
    request = urllib.request.Request(
        base + path,
        headers={"Authorization": key, "User-Agent": USER_AGENT,
                 "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, dict(response.headers), time.time() - started
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), time.time() - started
    except OSError as exc:
        return 0, {"_error": str(exc)}, time.time() - started


def burst(path, count, spacing, key, base, label):
    """Send `count` requests `spacing` seconds apart. Stop early on the second 429."""
    started = time.time()
    statuses, first_429, retry_after, seen_429 = [], None, None, 0
    for index in range(count):
        status, headers, _ = hit(path, key, base)
        offset = time.time() - started
        statuses.append(status)
        log({"ts": time.time(), "label": label, "path": path, "spacing": spacing,
             "index": index, "offset": round(offset, 3), "status": status,
             "retry_after": headers.get("Retry-After")})
        if status == 429:
            seen_429 += 1
            if first_429 is None:
                first_429 = index
                retry_after = headers.get("Retry-After")
            if seen_429 >= 2:
                break
        if spacing:
            time.sleep(spacing)
    elapsed = time.time() - started
    ok = sum(1 for s in statuses if s in (200, 400, 404))
    return {"spacing": spacing, "sent": len(statuses), "ok": ok,
            "first_429_at": first_429, "retry_after": retry_after,
            "elapsed": round(elapsed, 2),
            "rate": round(len(statuses) / elapsed, 2) if elapsed else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--phase0", action="store_true",
                        help="only check whether free 400s are rate limited")
    parser.add_argument("--count", type=int, default=45, help="requests per spacing")
    parser.add_argument("--confirm", type=float,
                        help="spend credits confirming one spacing on a billed endpoint")
    parser.add_argument("--cooldown", type=float, default=45.0,
                        help="seconds between spacings, so one burst does not poison the next")
    args = parser.parse_args()

    key, base = api_key(), base_url()
    print(f"base {base}   log {os.path.relpath(LOG, HERE)}")

    if args.confirm is not None:
        print(f"\nCONFIRM on {BILLED_PATH} at {args.confirm}s spacing — this spends credits")
        result = burst(BILLED_PATH, args.count, args.confirm, key, base, "confirm")
        print(json.dumps(result, indent=2))
        return

    print(f"\nPhase 0 — is the free path ({FREE_PATH}, 400) rate limited at all?")
    zero = burst(FREE_PATH, args.count, 0.0, key, base, "phase0")
    print(json.dumps(zero, indent=2))
    if zero["first_429_at"] is None:
        print("\nNo 429 on the free path even at full speed. Either the limiter sits behind "
              "billing, or the window is longer than this burst. Free bisection is not "
              "possible; re-run with --confirm on a billed endpoint instead.")
        return
    if args.phase0:
        return

    print(f"\nFirst 429 after {zero['first_429_at']} requests at "
          f"{zero['rate']} req/s. Bisecting spacing.")
    results = [zero]
    for spacing in (0.1, 0.25, 0.5, 1.0):
        print(f"\ncooling down {args.cooldown}s...")
        time.sleep(args.cooldown)
        print(f"spacing {spacing}s")
        result = burst(FREE_PATH, args.count, spacing, key, base, f"spacing-{spacing}")
        print(json.dumps(result, indent=2))
        results.append(result)
        if result["first_429_at"] is None:
            print(f"clean at {spacing}s — no need to slow down further")
            break

    print("\n| spacing | sent | first 429 at | achieved req/s | Retry-After |")
    print("| --- | --- | --- | --- | --- |")
    for r in results:
        print(f"| {r['spacing']}s | {r['sent']} | "
              f"{'none' if r['first_429_at'] is None else r['first_429_at']} | "
              f"{r['rate']} | {r['retry_after'] or '—'} |")


if __name__ == "__main__":
    main()


def recovery(key, base, poll=5.0, limit=240):
    """How long until the limiter lets a billed call through again.

    Polls one billed call every `poll` seconds. A 429 is free, so the wait costs nothing;
    only the single call that finally succeeds is billed.
    """
    started = time.time()
    attempts = 0
    while time.time() - started < limit:
        status, headers, _ = hit(BILLED_PATH, key, base)
        attempts += 1
        waited = round(time.time() - started, 1)
        log({"ts": time.time(), "label": "recovery", "path": BILLED_PATH,
             "offset": waited, "status": status,
             "retry_after": headers.get("Retry-After")})
        print(f"  t+{waited:6.1f}s  {status}")
        if status != 429:
            return {"recovered_after_s": waited, "attempts": attempts, "status": status}
        time.sleep(poll)
    return {"recovered_after_s": None, "attempts": attempts,
            "note": f"still limited after {limit}s"}
