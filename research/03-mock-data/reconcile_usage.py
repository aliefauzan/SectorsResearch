#!/usr/bin/env python3
"""
Reconcile the harness's own ledger against the portal's usage log.

The API returns no spend headers, so `est_cost` in `recorded/_ledger.jsonl` is a *model* of
what each call should have cost, never a measurement. The portal's usage-log export is the
only independent record — one row per request, with the credits actually charged.

    python3 reconcile_usage.py                       # uses ../99-raw/usage-log/*.csv
    python3 reconcile_usage.py ~/Downloads/*.csv     # or point it at a fresh export

Exit status is 1 when the totals disagree, so this can gate a release the same way
verify_mock.py does. Two caveats it handles for you:

  * The portal normalises `/v2/subsectors` (no trailing slash) onto `/v2/subsectors/`.
  * Traffic that never went through capture.py — the rate-limit probe, anything run by hand —
    appears in the portal and not in the ledger. Those paths are reported separately rather
    than counted as errors.
"""
import collections
import csv
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "recorded", "_ledger.jsonl")
DEFAULT_LOGS = os.path.join(HERE, "..", "99-raw", "usage-log", "*.csv")

# Paths the rate-limit probe hammered outside the ledger; a difference here is expected.
OUT_OF_BAND = {"/v2/subsectors/", "/v2/index-daily/klse/"}

# Two rows the ledger got wrong before this reconciliation existed, both fixed in code on
# 2026-09-06. They are listed rather than silently excluded: the ledger is append-only
# evidence, so the wrong numbers stay on the record and the fix is verified by any *new*
# call to these paths matching. Anything not in this dict is a live discrepancy.
KNOWN_HISTORICAL = {
    "/v2/broker-activity/AD/top/": (1, 2,
        "plan_live.py hardcoded 1 credit; the spec and the portal both say 2. It now reads "
        "declared costs out of fixtures/_index.json"),
    "/v2/does-not-exist/": (1, 0,
        "capture.py billed every 404. An unrouted path is free — only a routed 404 (the "
        "lookup ran) costs a credit. unrouted_404() now tells them apart"),
}


def load_portal(patterns):
    rows = []
    for pattern in patterns:
        for path in sorted(glob.glob(os.path.expanduser(pattern))):
            with open(path) as fh:
                rows.extend(list(csv.DictReader(fh)))
    return rows


def main():
    patterns = sys.argv[1:] or [DEFAULT_LOGS]
    portal_rows = load_portal(patterns)
    if not portal_rows:
        sys.exit(f"no usage-log CSVs matched {patterns}")

    portal = collections.Counter()
    for row in portal_rows:
        portal[row["endpoint"]] += int(row["credits_charged"])

    ledger = collections.Counter()
    with open(LEDGER) as fh:
        for line in fh:
            entry = json.loads(line)
            path = entry["path"]
            if not path.endswith("/"):
                path += "/"          # the portal normalises this; match it
            ledger[path] += entry["billed_cost"]

    print(f"portal rows: {len(portal_rows)}   portal total: {sum(portal.values())}")
    print(f"ledger total (capture only): {sum(ledger.values())}")
    print(f"difference (traffic outside capture.py): "
          f"{sum(portal.values()) - sum(ledger.values())}\n")

    mismatches = []
    for endpoint in sorted(set(portal) | set(ledger)):
        charged, modelled = portal.get(endpoint, 0), ledger.get(endpoint, 0)
        if charged != modelled and endpoint not in OUT_OF_BAND:
            mismatches.append((endpoint, modelled, charged))

    live = [m for m in mismatches if KNOWN_HISTORICAL.get(m[0], (None, None))[:2] != m[1:]]
    historical = [m for m in mismatches if m not in live]

    if historical:
        print(f"{len(historical)} known historical discrepancy(ies), already fixed in code:")
        for endpoint, modelled, charged in historical:
            print(f"  {endpoint}: ledger {modelled}, portal {charged} — "
                  f"{KNOWN_HISTORICAL[endpoint][2]}")
        print()
    if live:
        print(f"{len(live)} endpoint(s) where the model and the bill disagree:")
        print("| endpoint | ledger says | portal charged |")
        print("| --- | --- | --- |")
        for endpoint, modelled, charged in live:
            print(f"| `{endpoint}` | {modelled} | {charged} |")
    else:
        print("no unexplained discrepancy: every other endpoint's modelled cost matches "
              "what the portal charged")

    by_status = collections.defaultdict(int)
    counts = collections.Counter()
    for row in portal_rows:
        by_status[row["http_status"]] += int(row["credits_charged"])
        counts[row["http_status"]] += 1
    print("\n| status | requests | credits |")
    print("| --- | --- | --- |")
    for status in sorted(counts):
        print(f"| {status} | {counts[status]} | {by_status[status]} |")
    print("\n429 and 403 do not appear in the log at all — they are rejected before "
          "accounting, which is why they cost nothing.")

    return 1 if live else 0


if __name__ == "__main__":
    sys.exit(main())
