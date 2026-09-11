#!/usr/bin/env python3
"""
Fiscal quarters, and which quarter a number is allowed to be compared against.

Pure: no I/O, no HTTP, no file paths, and nothing imported from `sources`. The whole
module exists because two quarters that look adjacent on a page are not necessarily
comparable, and because the *label* on a comparison is as load-bearing as the number.

    from periods import period_key, select_comparator, COMPARATOR_LABEL

    period_key("2026-03-31")                       -> "q1-2026"
    select_comparator("q1-2026", keys, "yoy")      -> ("q1-2025", "unavailable",
                                                       "comparator_unavailable")

Three facts this file is built on, all measured against the 2026-09-06 capture:

  1. IDX quarterly dates are **period-end** dates (`2026-03-31`), not filing dates. The
     quarter is therefore derivable from the month, and only from months 3, 6, 9 and 12.
     A non-calendar fiscal year would break that mapping, so an unexpected month raises
     `UnknownPeriod` rather than being rounded to the nearest quarter. None of the four
     recorded symbols has one.
  2. Neither source can be trusted for the quarter *label*. `recorded/` carries none at
     all for the quarterly payload and `"q1"` lowercase in the trigger sweep; `synth/`
     carries `"Q1"` in the trigger sweep and `"Q1-2025"` in the quarterly payload. Every
     key in this product is derived from the date.
  3. On `recorded/` the prior-year quarter does not exist — only four trailing quarters
     were captured. `select_comparator` returns `unavailable` for it, which is a result,
     not an error: `metrics.py` turns it into `unknown` and `template.py` names the call
     that would supply it.

    python3 periods.py    # rollover, an FY date, an unknown month, an empty universe
"""
import datetime

#: Period-end month -> quarter number. Nothing else is a quarter end on IDX.
QUARTER_END_MONTH = {3: 1, 6: 2, 9: 3, 12: 4}

#: The two comparator modes PRD §9 allows. The default is year-over-year; sequential is
#: an explicit Admin opt-in, because "vs last quarter" flatters a seasonal business.
COMPARATOR_MODES = ("yoy", "sequential")

#: The wording is load-bearing. A sequential comparison narrated with year-over-year
#: wording is a factual error that looks completely fine on screen, so the label travels
#: with the comparator and `gate.comparator_mislabelled` checks that it was used.
COMPARATOR_LABEL = {
    "yoy": "vs kuartal yang sama tahun lalu",
    "sequential": "vs kuartal sebelumnya (perbandingan berurutan, diaktifkan Admin)",
}

#: Wording that may only appear beside a `yoy` comparator. `gate.py` imports this list
#: rather than keeping its own copy, so the two can never drift apart.
YOY_WORDING = ("yoy", "year-on-year", "year over year", "tahun lalu",
               "tahun sebelumnya", "yoy.")


class UnknownPeriod(Exception):
    """A date that is not an IDX quarter end.

    Raised rather than inferring a quarter, because inferring one is how a company with
    a June fiscal year end silently gets its Q2 narrated as Q4. The caller sees the raw
    date and can say *belum diambil*; this module refuses to guess on its behalf.
    """


def period_key(date_str):
    """`"2026-03-31"` -> `"q1-2026"`. Derived from the month, never from a label."""
    if not date_str:
        raise UnknownPeriod("no date given")
    try:
        date = datetime.date.fromisoformat(str(date_str)[:10])
    except ValueError as exc:
        raise UnknownPeriod(f"{date_str!r} is not a date") from exc
    if date.month not in QUARTER_END_MONTH:
        raise UnknownPeriod(
            f"{date_str} is not a quarter end — month {date.month:02d} is not one of "
            f"{sorted(QUARTER_END_MONTH)}; a non-calendar fiscal year is not supported")
    return f"q{QUARTER_END_MONTH[date.month]}-{date.year}"


def split_key(key):
    """`"q1-2026"` -> `(1, 2026)`. Raises on anything this module did not produce."""
    try:
        quarter, year = key.split("-")
        return int(quarter[1:]), int(year)
    except (AttributeError, ValueError) as exc:
        raise UnknownPeriod(f"{key!r} is not a period key") from exc


def prior_year_same_quarter(key):
    """`"q1-2026"` -> `"q1-2025"`. The PRD §9 default comparator."""
    quarter, year = split_key(key)
    return f"q{quarter}-{year - 1}"


def prior_sequential(key):
    """`"q1-2026"` -> `"q4-2025"`. Rolls the year at q1, which is the whole edge case."""
    quarter, year = split_key(key)
    return f"q4-{year - 1}" if quarter == 1 else f"q{quarter - 1}-{year}"


def comparator_key(target_key, mode):
    """The key `mode` would compare `target_key` against, present or not."""
    if mode not in COMPARATOR_MODES:
        raise UnknownPeriod(f"unknown comparator mode {mode!r}")
    return (prior_year_same_quarter(target_key) if mode == "yoy"
            else prior_sequential(target_key))


def select_comparator(target_key, available_keys, mode="yoy"):
    """`(comparator_key, status, reason_code)` for a target period.

    `status` is `"ok"` or `"unavailable"`. An unavailable comparator is a first-class
    result: it names the period that is missing, so the caller can say which call would
    supply it instead of rendering a zero.
    """
    wanted = comparator_key(target_key, mode)
    if wanted in set(available_keys or ()):
        return wanted, "ok", None
    return wanted, "unavailable", "comparator_unavailable"


def label_sentence(mode):
    """The comparator label as a sentence. `str.capitalize()` would lowercase "Admin"."""
    label = COMPARATOR_LABEL[mode]
    return label[0].upper() + label[1:]


def quarter_label(key):
    """`"q1-2026"` -> `"Q1 2026"`, for a sentence rather than a dict key."""
    quarter, year = split_key(key)
    return f"Q{quarter} {year}"


# ------------------------------------------------------------------------------ gates


def check_period_key():
    """Every quarter end maps, and nothing else does."""
    failures = []
    cases = [("2026-03-31", "q1-2026"), ("2026-06-30", "q2-2026"),
             ("2025-09-30", "q3-2025"), ("2025-12-31", "q4-2025"),
             ("2026-03-31T00:00:00", "q1-2026")]
    for date_str, expected in cases:
        got = period_key(date_str)
        if got != expected:
            failures.append(f"{date_str}: {got}, expected {expected}")

    # A December 31 FY date is a real quarter end and must NOT be special-cased away:
    # the fourth quarter and the full year share a period-end date on IDX.
    if period_key("2025-12-31") != "q4-2025":
        failures.append("the FY period end stopped reading as q4")

    bad = ["2026-05-31", "2026-01-31", "", None, "not-a-date", "2026-13-31"]
    for date_str in bad:
        try:
            period_key(date_str)
        except UnknownPeriod:
            continue
        failures.append(f"a non-quarter-end was accepted: {date_str!r}")
    return failures, len(cases) + len(bad) + 1


def check_rollover():
    """q1 -> q4 of the previous year is the one arithmetic that is easy to get wrong."""
    failures = []
    cases = [("q1-2026", "q4-2025"), ("q2-2026", "q1-2026"),
             ("q3-2026", "q2-2026"), ("q4-2026", "q3-2026")]
    for key, expected in cases:
        got = prior_sequential(key)
        if got != expected:
            failures.append(f"prior_sequential({key}) = {got}, expected {expected}")
    if prior_year_same_quarter("q1-2026") != "q1-2025":
        failures.append("prior_year_same_quarter lost a year")
    try:
        split_key("2026-q1")
    except UnknownPeriod:
        pass
    else:
        failures.append("a malformed period key was parsed")
    return failures, len(cases) + 2


def check_selection():
    """The recorded situation, stated as a test: yoy is unavailable, sequential is not."""
    failures = []
    adro = ["q1-2026", "q4-2025", "q3-2025", "q2-2025"]      # the real ADRO window

    key, status, reason = select_comparator("q1-2026", adro, "yoy")
    if (key, status, reason) != ("q1-2025", "unavailable", "comparator_unavailable"):
        failures.append(f"yoy on recorded ADRO: {(key, status, reason)}")

    key, status, reason = select_comparator("q1-2026", adro, "sequential")
    if (key, status, reason) != ("q4-2025", "ok", None):
        failures.append(f"sequential on recorded ADRO: {(key, status, reason)}")

    # An empty universe must be a clean `unavailable`, not an IndexError.
    key, status, reason = select_comparator("q1-2026", [], "yoy")
    if status != "unavailable":
        failures.append("an empty availability set did not read as unavailable")
    key, status, reason = select_comparator("q1-2026", None, "yoy")
    if status != "unavailable":
        failures.append("a None availability set did not read as unavailable")

    # The synthetic window has three years, so yoy resolves there.
    synth = ["q3-2026", "q2-2026", "q1-2026", "q4-2025", "q3-2025", "q2-2025",
             "q1-2025", "q4-2024"]
    key, status, reason = select_comparator("q1-2026", synth, "yoy")
    if (key, status) != ("q1-2025", "ok"):
        failures.append(f"yoy on synth: {(key, status)}")

    try:
        select_comparator("q1-2026", synth, "quarterly-ish")
    except UnknownPeriod:
        pass
    else:
        failures.append("an unknown comparator mode was accepted")
    return failures, 6


def check_labels():
    """The two labels must stay distinguishable, and only one may carry YoY wording."""
    failures = []
    if set(COMPARATOR_LABEL) != set(COMPARATOR_MODES):
        failures.append("a comparator mode has no label")
    sequential = COMPARATOR_LABEL["sequential"].lower()
    for word in YOY_WORDING:
        if word in sequential:
            failures.append(f"the sequential label contains YoY wording: {word!r}")
    if "tahun lalu" not in COMPARATOR_LABEL["yoy"]:
        failures.append("the yoy label no longer says which year it compares against")
    return failures, len(YOY_WORDING) + 2


def main():
    results = [("period keys", *check_period_key()),
               ("year rollover", *check_rollover()),
               ("comparator selection", *check_selection()),
               ("comparator labels", *check_labels())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nevery period key is derived from a date, never from a label" if not failed
          else f"\n{failed} period failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
