#!/usr/bin/env python3
"""
Every number the verdict turns on, in one file, with the reason it has that value.

A threshold buried in the function that uses it is a threshold nobody can audit. These
are named, printed on the method page, and read by `learn.py` when calibration moves
one — so a judge can see both the value shipped and the value the replay argued for.

    python3 thresholds.py     # print the table, then the gates

Calibration writes to `state/thresholds.learned.json`; this file is the floor and the
ceiling. `clamp()` is what stops a learning loop from walking a threshold somewhere
indefensible, which is the failure mode every self-tuning system has.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LEARNED = os.path.join(HERE, "state", "thresholds.learned.json")

#: name -> (shipped value, floor, ceiling, why this value)
TABLE = {
    # --- Pilar 1 · konsentrasi -------------------------------------------------
    "top1_dominant": (0.40, 0.25, 0.60,
                      "One broker taking 40% of net buying is the point where 'the market "
                      "bought it' stops being a fair description of what happened."),
    "neff_dominant": (3.0, 2.0, 5.0,
                      "Effective buyers = 1/HHI. Below 3 the buying side is a handful of "
                      "desks however many broker codes appear in the file."),
    "neff_crowd": (8.0, 5.0, 15.0,
                   "Above 8 effective buyers no single hand explains the move."),
    "foreign_share_in": (0.60, 0.50, 0.80,
                         "Foreign brokers taking 60% of net buying is a one-sided tape, and "
                         "it has to agree with net_foreign_inflow before it is said out loud."),
    "retail_crowd_share": (0.60, 0.45, 0.80,
                           "Retail plus mixed above 60% is the signature of a crowd, not a desk."),

    # --- Pilar 2 · volume ------------------------------------------------------
    "volume_z": (2.0, 1.5, 3.5,
                 "Robust z on log volume. 2.0 keeps the daily flag count survivable for a "
                 "human reader; the MAD floor below stops a dead stock manufacturing one."),
    "volume_mad_floor": (0.05, 0.01, 0.30,
                         "One log tick. Without a floor, a stock whose volume never moves "
                         "has MAD≈0 and every ordinary day scores z=∞."),

    # --- Pilar 3 · momentum ----------------------------------------------------
    "resid_z": (2.5, 1.5, 4.0,
                "Cumulative 3-day residual return against IHSG, robust z over a 45-day "
                "baseline. 2.5 is the level where the move stops being the index's."),
    "price_mad_floor": (0.005, 0.001, 0.02,
                        "Half a percent of daily log return. Same argument as volume."),
    "beta_shrink": (0.70, 0.50, 1.00,
                    "beta_eff = 0.70*beta_OLS + 0.30. Shrinking towards 1 stops a thin "
                    "baseline from handing a stock a beta of 4 and erasing its own move."),
    "baseline_days": (45, 30, 60,
                      "Trading days of baseline. 45 plus a 10-day scan plus the 3-day "
                      "exclusion fits one /v2/daily/ call, which caps at 90 days."),
    "event_window": (3, 1, 5,
                     "Trading days the move and the flow are both measured over. Broker "
                     "summary is daily; three days is long enough to survive one quiet session."),
    "dead_day_share": (0.40, 0.20, 0.70,
                       "More than 40% zero-return days in the baseline and no z means "
                       "anything. Such symbols are rejected with a reason, not scored."),

    # --- Pilar 4 · katalis -----------------------------------------------------
    "news_lookback_days": (7, 3, 21,
                           "How far before the flagged day an article may sit and still be "
                           "read as preceding the move."),
    "filing_lookback_days": (30, 7, 90,
                             "Insider and major-holder filings are reported with a lag; "
                             "30 days is the window where one still explains today's tape."),
    "filing_material_pct": (0.5, 0.1, 2.0,
                            "Percentage points of the company a registered holder moved "
                            "before it is worth putting on the card."),

    # --- structure modifiers ---------------------------------------------------
    "thin_float": (0.15, 0.05, 0.30,
                   "Free float under 15% is the population where a small rupiah amount "
                   "moves the price a long way."),
    "float_absorbed": (0.01, 0.002, 0.05,
                       "1% of free float changing hands inside the event window. This is "
                       "the sentence no other service can print."),
}

#: Reject reasons, so a skipped symbol is a named outcome and not a silent gap.
REJECTS = {
    "baseline_tipis": "fewer baseline days than baseline_days requires",
    "baseline_mati": "more zero-return days than dead_day_share allows",
    "tanpa_broker": "no broker summary on this source for this symbol",
    "tanpa_indeks": "no IHSG series to take the market move out of",
    "tanpa_float": "symbol absent from /v2/free-float/",
}


def _learned():
    if not os.path.exists(LEARNED):
        return {}
    try:
        with open(LEARNED) as handle:
            return json.load(handle).get("values", {})
    except (ValueError, OSError):
        return {}


def clamp(name, value):
    """Hold a proposed value inside the floor/ceiling this table declares."""
    _, low, high, _ = TABLE[name]
    return max(low, min(high, value))


def get(name):
    """The value in force: the calibrated one when it exists and is in range, else shipped."""
    shipped, _, _, _ = TABLE[name]
    proposed = _learned().get(name)
    return clamp(name, proposed) if isinstance(proposed, (int, float)) else shipped


def provenance(name):
    """`('learned', v)` or `('shipped', v)` — the card says which, so nothing is implied."""
    proposed = _learned().get(name)
    if isinstance(proposed, (int, float)):
        return "learned", clamp(name, proposed)
    return "shipped", TABLE[name][0]


def check_table():
    failures = []
    for name, (shipped, low, high, why) in TABLE.items():
        if not low <= shipped <= high:
            failures.append(f"{name}: shipped {shipped} outside [{low}, {high}]")
        if len(why) < 40:
            failures.append(f"{name}: reason too short to audit")
        if clamp(name, high * 10) != high or clamp(name, low / 10) != low:
            failures.append(f"{name}: clamp does not hold the bounds")
    return failures, len(TABLE)


def check_learned_cannot_escape():
    """A calibration file asking for something absurd must not change the value used."""
    failures = []
    for name, (_, low, high, _) in TABLE.items():
        if clamp(name, high + 1000) > high or clamp(name, low - 1000) < low:
            failures.append(f"{name}: a runaway calibration escaped its bounds")
    return failures, 1


def main():
    width = max(len(n) for n in TABLE)
    for name in TABLE:
        origin, value = provenance(name)
        _, low, high, why = TABLE[name]
        print(f"{name:<{width}}  {value:<8} [{low}, {high}]  {origin:<7} {why.splitlines()[0][:60]}")
    print()
    total = 0
    bad = []
    for check in (check_table, check_learned_cannot_escape):
        failures, count = check()
        total += count
        bad += failures
    for line in bad:
        print("FAIL", line)
    print(f"{total - len(bad)}/{total} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
