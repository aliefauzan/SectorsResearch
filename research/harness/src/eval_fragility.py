#!/usr/bin/env python3
"""
Score the rule against labels, and refuse to flatter it.

    python3 src/eval_fragility.py --source synth
    python3 src/eval_fragility.py --source recorded

Positives are suspensions whose `reason` matches the pump vocabulary for that source.
Negatives are 2-SD volume spikes with no suspension inside the following 10 trading
days — spikes that went nowhere, which is the only honest comparison class, because
scoring against every quiet day would make any rule look excellent.

**Precision and recall, split by market-cap bucket. Never accuracy.** Suspensions are
rare; a model that answers "not fragile" to everything scores above 97% accuracy on
this data and is worth nothing. The split by bucket is correction K2: a rule tuned on
large caps and reported as one number hides that it does not transfer to the small
caps where pumps actually happen.

**Scored at T−1.** Every feature comes from strictly before the event date, so the
suspension itself — and the price move on the day it lands — cannot leak into the
score that is supposed to predict it. The leak check is an assertion, not a comment.

The honest caveat is the headline, not a footnote: `synth/` contains **no planted pump
events**. Its suspensions and its price series are generated independently, so a
positive here is a coincidence and the recall column below is measuring nothing. It is
run anyway because it proves the harness works end to end; the numbers become real
only after the ~30-credit Phase 2 pull of the remaining 563 suspension reasons.

Exit status is 1 when the evaluation itself is broken — a detected leak, or no
scoreable positives — and 0 when it ran, including when it ran on data whose numbers
mean nothing. Uninterpretable is not the same as failed, and conflating them would
make the gate useless.
"""
import argparse
import collections
import glob
import json
import os
import sys

import fragility
import sources

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.dirname(HERE)

#: Rupiah market-cap bucket edges (K2). Chosen from the synthetic distribution —
#: min 1.8T, median 187.6T — so that all three buckets are populated and the split can
#: actually be read. The real IDX distribution is far more bottom-heavy; these edges are
#: a starting point for Phase 2, not a finding.
BUCKETS = [("small  <Rp50T", 0, 50e12),
           ("mid    Rp50–500T", 50e12, 500e12),
           ("large  ≥Rp500T", 500e12, float("inf"))]

QUIET_DAYS = 10


def bucket_of(market_cap):
    if not market_cap:
        return "unknown"
    for name, low, high in BUCKETS:
        if low <= market_cap < high:
            return name
    return "unknown"


def load_series(source):
    """Every daily series this source holds, as `{symbol: [rows sorted by date]}`."""
    series = {}
    if source == "synth":
        paths = glob.glob(os.path.join(HARNESS, "synth", "market", "daily", "*.json"))
    else:
        paths = glob.glob(os.path.join(HARNESS, "recorded", "v2_daily_*.json"))
    for path in paths:
        with open(path) as handle:
            rows = [sources.normalize_daily(r) for r in json.load(handle)]
        rows = sorted((r for r in rows if r["date"] and r["close"] is not None),
                      key=lambda r: r["date"])
        if rows:
            series[rows[0]["symbol"]] = rows
    return series


def load_labels(source):
    """Pump-labelled suspensions as `{symbol: [dates]}`, plus every suspension date."""
    payload = sources.load(source, "suspensions")
    positives = collections.defaultdict(list)
    any_suspension = collections.defaultdict(list)
    for raw in sources.results_of(payload):
        row = sources.normalize_suspension(raw)
        if not row["symbol"] or not row["suspension_date"]:
            continue
        any_suspension[row["symbol"]].append(row["suspension_date"])
        if sources.is_pump_label(row["reason"], source):
            positives[row["symbol"]].append(row["suspension_date"])
    return positives, any_suspension


def index_before(rows, date):
    """Position of the last trading row strictly before `date` — the T−1 rule."""
    prior = [i for i, r in enumerate(rows) if r["date"] < date]
    return prior[-1] if prior else None


def score_at(rows, index):
    """Was the rule fragile at `rows[index]`, using only rows up to and including it?

    The slice is the leak guard: `score_price_volume` is handed nothing after the test
    day, so no later row can reach the baseline even by accident.
    """
    window = rows[:index + 1]
    axes = fragility.score_price_volume(window, rows[index]["date"])
    if not all(a.evaluated for a in axes):
        return None
    return all(a.fragile for a in axes)


def evaluate(source):
    """Score every positive at T−1 and every quiet spike, bucketed by market cap."""
    series = load_series(source)
    positives, any_suspension = load_labels(source)

    stats = collections.defaultdict(lambda: collections.Counter())
    skipped = collections.Counter()

    for symbol, dates in positives.items():
        rows = series.get(symbol)
        if not rows:
            skipped["no daily series"] += 1
            continue
        for date in dates:
            index = index_before(rows, date)
            if index is None:
                skipped["suspension precedes the capture window"] += 1
                continue
            verdict = score_at(rows, index)
            if verdict is None:
                skipped["not enough baseline at T-1"] += 1
                continue
            bucket = bucket_of(rows[index]["market_cap"])
            stats[bucket]["TP" if verdict else "FN"] += 1

    for symbol, rows in series.items():
        suspensions = any_suspension.get(symbol, [])
        for index in range(fragility.BASELINE_DAYS, len(rows)):
            verdict = score_at(rows, index)
            if not verdict:
                continue
            date = rows[index]["date"]
            horizon = rows[min(index + QUIET_DAYS, len(rows) - 1)]["date"]
            if any(date < s <= horizon for s in suspensions):
                continue          # a spike that was followed by a suspension is not quiet
            stats[bucket_of(rows[index]["market_cap"])]["FP"] += 1

    return stats, skipped, series, positives


def check_leakage(series, positives):
    """Prove T−1 scoring cannot see the event: a forged post-event row must change nothing."""
    for symbol, dates in positives.items():
        rows = series.get(symbol)
        if not rows or not dates:
            continue
        index = index_before(rows, dates[0])
        if index is None or index < fragility.BASELINE_DAYS:
            continue
        before = score_at(rows, index)
        poisoned = [dict(r) for r in rows]
        for row in poisoned[index + 1:]:
            row["close"], row["volume"] = row["close"] * 100, row["volume"] * 100
        if score_at(poisoned, index) != before:
            return f"{symbol}: a post-event row changed the T-1 score — the feature window leaks"
    return None


def report(source, stats, skipped, leak):
    buckets = [name for name, _, _ in BUCKETS] + ["unknown"]
    print(f"\n| market cap | TP | FN | FP | precision | recall |")
    print("| --- | --- | --- | --- | --- | --- |")
    total = collections.Counter()
    for name in buckets:
        row = stats.get(name)
        if not row:
            continue
        total.update(row)
        tp, fn, fp = row["TP"], row["FN"], row["FP"]
        precision = f"{tp / (tp + fp):.2f}" if tp + fp else "n/a"
        recall = f"{tp / (tp + fn):.2f}" if tp + fn else "n/a"
        print(f"| {name} | {tp} | {fn} | {fp} | {precision} | {recall} |")
    tp, fn, fp = total["TP"], total["FN"], total["FP"]
    precision = f"{tp / (tp + fp):.2f}" if tp + fp else "n/a"
    recall = f"{tp / (tp + fn):.2f}" if tp + fn else "n/a"
    print(f"| **all** | {tp} | {fn} | {fp} | **{precision}** | **{recall}** |")
    print("\nAccuracy is deliberately not reported: answering \"not fragile\" to everything "
          "scores above 97% on this data.")

    if skipped:
        print("\nnot scored:")
        for reason, count in skipped.most_common():
            print(f"  {count:4}  {reason}")

    print(f"\nleak check: {'PASS — T-1 features cannot see the event' if not leak else 'FAIL — ' + leak}")

    if source == "synth":
        print("\n*** THESE NUMBERS MEAN NOTHING. ***\n"
              "synth/ contains no planted pump events: its suspensions and its price series\n"
              "are generated independently, so every TP above is a coincidence and recall is\n"
              "measuring noise. This run proves the harness works end to end and nothing else.\n"
              "Real numbers need the ~30-credit Phase 2 pull of the 563 unread suspension reasons.")
    else:
        print(f"\nlabels come from the {len(sources.LABEL_VOCAB['real'])}-term real vocabulary over "
              "the 20 suspensions that were captured. The other 563 reasons are unread, so recall "
              "here is recall against a 20-row sample, not against the IDX.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--source", default="synth", choices=["synth", "recorded"],
                        help="which layer to evaluate against (default: synth)")
    args = parser.parse_args(argv)

    stats, skipped, series, positives = evaluate(args.source)
    leak = check_leakage(series, positives)
    report(args.source, stats, skipped, leak)

    scoreable = sum(stats[b]["TP"] + stats[b]["FN"] for b in stats)
    if leak:
        print("\nexit 1: the evaluation leaks and cannot be trusted")
        return 1
    if not scoreable:
        print(f"\nexit 1: no positive was scoreable on --source {args.source} — "
              "the label set and the price series do not overlap")
        return 1
    print(f"\nevaluation ran: {scoreable} positive(s) scored at T-1, "
          f"{sum(stats[b]['FP'] for b in stats)} quiet spike(s) counted against it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
