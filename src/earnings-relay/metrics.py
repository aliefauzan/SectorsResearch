#!/usr/bin/env python3
"""
The three metrics, and nothing else.

Pure: no I/O, no HTTP, no file paths, no imports from `sources`. Give it two numbers and
it gives back a result dict; give it a number it cannot divide by and it gives back
`unknown` with the reason. It never returns zero for "we do not know", and it never
returns a percentage for a comparison it could not make.

    from metrics import revenue_yoy, net_income_yoy, net_margin_delta, direction

    revenue_yoy(8_004_471_444_300, None)
    -> {"type": "revenue_yoy", "value": None, "display": None,
        "status": "unknown", "reason_code": "missing_input", …}

PRD §9, implemented literally:

  * Revenue YoY = revenue_t / revenue_prior − 1. Prior null or zero -> `unknown`, and it
    may not be narrated as a percentage.
  * Net Income YoY uses the same period. A sign change is reported as `sign_change` with
    the absolute values, never as a growth percentage — "-340% growth" for a swing from
    profit to loss is the exact failure this rule exists to stop.
  * Net Margin Delta = (ni_t / rev_t) − (ni_prior / rev_prior), in **percentage points**,
    not percent. Either denominator zero or null -> `unknown`.
  * Rounding happens at the display layer. `direction()` is computed on the UNROUNDED
    value, so a +0,04% quarter reads "naik" while its display rounds to "0,0%".

Every result carries the formula it used and the comparator it was computed against, so
`factset.py` can lock them and the evidence drawer can print them without recomputing
anything.

    python3 metrics.py    # null, zero, sign change, rounding boundary, real vectors
"""

#: `quality_status` in PRD §13's Metric entity. Three values, and no fourth: anything a
#: metric cannot say is `unknown` with a reason code, never a silent zero.
OK = "ok"
UNKNOWN = "unknown"
SIGN_CHANGE = "sign_change"

#: Why a metric is not `ok`. These strings reach the UI and the audit log verbatim.
MISSING_INPUT = "missing_input"
DENOMINATOR_ZERO = "denominator_zero"
NOT_A_NUMBER = "not_a_number"

FORMULA = {
    "revenue_yoy": "revenue_t / revenue_prior - 1",
    "net_income_yoy": "net_income_t / net_income_prior - 1",
    "net_margin_delta": "(net_income_t / revenue_t) - (net_income_prior / revenue_prior)",
}

#: Display precision. One decimal for a percentage, one for percentage points — the
#: source precision stays in `inputs`, which is what the evidence drawer shows.
PLACES = 1


def _number(value):
    """The value as a float, or None. A bool is not a number, whatever Python thinks."""
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    # NaN and infinity arrive from a JSON payload as strings and from arithmetic as
    # floats; both are unusable and neither compares usefully.
    if out != out or out in (float("inf"), float("-inf")):
        return None
    return out


def direction(value):
    """`"naik" | "turun" | "datar"`, on the UNROUNDED value (PRD §9).

    The comparison is deliberately strict on both sides: `-0.0 == 0` is True in Python,
    so a negative zero reads `datar` rather than `turun`, which is the intended side —
    a change of exactly nothing is not a fall.
    """
    number = _number(value)
    if number is None:
        return None
    if number > 0:
        return "naik"
    if number < 0:
        return "turun"
    return "datar"


def round_display(value, places=PLACES, suffix="%"):
    """A ratio as an Indonesian-formatted percentage. Display only, never compared."""
    number = _number(value)
    if number is None:
        return None
    text = f"{number * 100:.{places}f}".replace(".", ",")
    return f"{text}{suffix}"


def points_display(value, places=PLACES):
    """A ratio difference as percentage points. `"1,2 poin persentase"`, not `"1,2%"`."""
    number = _number(value)
    if number is None:
        return None
    text = f"{number * 100:.{places}f}".replace(".", ",")
    return f"{text} poin persentase"


def _why_not_a_number(*pairs):
    """`not_a_number` when a value was supplied and unusable, `missing_input` when absent.

    The two are different findings: a null field is the vendor saying it has nothing,
    while a field that arrived as `"n/a"` is a schema change nobody noticed. PRD §10
    treats only the first as ordinary.
    """
    for raw, parsed in pairs:
        if raw is not None and parsed is None:
            return NOT_A_NUMBER
    return MISSING_INPUT


def _result(metric_type, value, display, status, reason_code, inputs, comparator,
            render_absolute=False):
    return {
        "type": metric_type,
        "value": value,
        "display": display,
        "status": status,
        "reason_code": reason_code,
        "inputs": inputs,
        "formula": FORMULA[metric_type],
        "comparator": comparator,
        # `template.py` reads this instead of inventing its own sign-change rule: a
        # sign change is rendered as two absolute figures, never as a growth rate.
        "render_absolute": render_absolute,
    }


def _growth(metric_type, current, prior, comparator, sign_aware):
    """Shared body of the two growth metrics. Not called directly."""
    inputs = {"current": current, "prior": prior}
    now, before = _number(current), _number(prior)

    if now is None or before is None:
        return _result(metric_type, None, None, UNKNOWN,
                       _why_not_a_number((current, now), (prior, before)),
                       inputs, comparator)
    if before == 0:
        return _result(metric_type, None, None, UNKNOWN, DENOMINATOR_ZERO, inputs,
                       comparator)
    if sign_aware and ((now < 0) != (before < 0)):
        # A profit that became a loss. The ratio is arithmetically fine and narratively
        # false, so no value is returned at all — only the two magnitudes.
        return _result(metric_type, None, None, SIGN_CHANGE, None, inputs, comparator,
                       render_absolute=True)

    value = now / before - 1
    return _result(metric_type, value, round_display(value), OK, None, inputs,
                   comparator)


def revenue_yoy(rev_t, rev_prior, comparator="yoy"):
    """Revenue growth against the comparator period. Prior null or zero -> `unknown`."""
    return _growth("revenue_yoy", rev_t, rev_prior, comparator, sign_aware=False)


def net_income_yoy(ni_t, ni_prior, comparator="yoy"):
    """Net income growth. A sign change is `sign_change`, never a growth percentage."""
    return _growth("net_income_yoy", ni_t, ni_prior, comparator, sign_aware=True)


def net_margin_delta(ni_t, rev_t, ni_prior, rev_prior, comparator="yoy"):
    """Net margin change in PERCENTAGE POINTS. Either denominator zero/null -> `unknown`."""
    inputs = {"net_income_current": ni_t, "revenue_current": rev_t,
              "net_income_prior": ni_prior, "revenue_prior": rev_prior}
    raw = (ni_t, rev_t, ni_prior, rev_prior)
    values = [_number(v) for v in raw]
    if any(v is None for v in values):
        return _result("net_margin_delta", None, None, UNKNOWN,
                       _why_not_a_number(*zip(raw, values)), inputs, comparator)
    now_ni, now_rev, before_ni, before_rev = values
    if now_rev == 0 or before_rev == 0:
        return _result("net_margin_delta", None, None, UNKNOWN, DENOMINATOR_ZERO,
                       inputs, comparator)
    value = (now_ni / now_rev) - (before_ni / before_rev)
    return _result("net_margin_delta", value, points_display(value), OK, None, inputs,
                   comparator)


def unavailable(metric_type, comparator, reason_code, inputs=None):
    """The result for a comparison whose comparator period does not exist at all.

    Separate from `_growth` because the reason is different in kind: the inputs were not
    null, they were never fetched. `template.py` renders this by naming the endpoint that
    would supply them.
    """
    return _result(metric_type, None, None, UNKNOWN, reason_code, inputs or {},
                   comparator)


METRIC_TYPES = tuple(FORMULA)


# ------------------------------------------------------------------------------ gates


def check_normal():
    """The happy path, on the real ADRO and BBCA vectors from the recordings."""
    failures = []
    # ADRO q1-2026 vs q4-2025 (sequential — the only comparison recorded data supports).
    adro = revenue_yoy(8004471444300, 8792499261000, comparator="sequential")
    if adro["status"] != OK:
        failures.append(f"ADRO revenue: {adro['status']}")
    if not (-0.0897 < adro["value"] < -0.0895):
        failures.append(f"ADRO revenue value drifted: {adro['value']}")
    if adro["display"] != "-9,0%":
        failures.append(f"ADRO revenue display: {adro['display']}")
    if direction(adro["value"]) != "turun":
        failures.append("ADRO revenue direction is not turun")

    # BBCA q2-2026 vs q1-2026.
    bbca = net_income_yoy(14861321000000, 14695475000000, comparator="sequential")
    if bbca["status"] != OK or direction(bbca["value"]) != "naik":
        failures.append(f"BBCA net income: {bbca['status']} {bbca['value']}")

    margin = net_margin_delta(2178080414220, 8004471444300,
                              2445263751840, 8792499261000, comparator="sequential")
    if margin["status"] != OK:
        failures.append(f"ADRO margin: {margin['status']}")
    if "poin persentase" not in (margin["display"] or ""):
        failures.append(f"the margin delta is not in percentage points: {margin['display']}")
    if "%" in (margin["display"] or ""):
        failures.append("the margin delta rendered a percent sign — it is points")

    for result in (adro, bbca, margin):
        if result["formula"] not in FORMULA.values():
            failures.append(f"{result['type']}: no formula stamped")
        if result["comparator"] != "sequential":
            failures.append(f"{result['type']}: comparator not carried through")
    return failures, 10


def check_missing_and_zero():
    """Null and zero are `unknown` with distinguishable reasons, and never a percentage."""
    failures = []
    cases = [
        (revenue_yoy(8e12, None), MISSING_INPUT, "null prior"),
        (revenue_yoy(None, 8e12), MISSING_INPUT, "null current"),
        (revenue_yoy(8e12, 0), DENOMINATOR_ZERO, "zero prior"),
        (revenue_yoy(8e12, 0.0), DENOMINATOR_ZERO, "zero float prior"),
        (revenue_yoy(8e12, "tidak ada"), NOT_A_NUMBER, "non-numeric prior"),
        (net_income_yoy(100, None), MISSING_INPUT, "null prior income"),
        (net_income_yoy(100, 0), DENOMINATOR_ZERO, "zero prior income"),
        (net_margin_delta(100, 0, 100, 1000), DENOMINATOR_ZERO, "zero revenue"),
        (net_margin_delta(100, 1000, 100, 0), DENOMINATOR_ZERO, "zero prior revenue"),
        (net_margin_delta(100, 1000, None, 1000), MISSING_INPUT, "null prior income"),
        (net_margin_delta(100, None, 100, 1000), MISSING_INPUT, "null revenue"),
    ]
    for result, reason, why in cases:
        if result["status"] != UNKNOWN:
            failures.append(f"{why}: status {result['status']}, expected unknown")
        if result["reason_code"] != reason:
            failures.append(f"{why}: reason {result['reason_code']}, expected {reason}")
        if result["value"] is not None or result["display"] is not None:
            failures.append(f"{why}: an unknown carried a value — {result['display']!r}")
        if "%" in str(result["display"]):
            failures.append(f"{why}: an unknown rendered a percentage")
    if direction(None) is not None:
        failures.append("direction() invented a direction for a missing value")
    return failures, len(cases) + 1


def check_sign_change():
    """A profit that became a loss must never be narrated as a growth percentage."""
    failures = []
    swing = net_income_yoy(-500, 1000)
    if swing["status"] != SIGN_CHANGE:
        failures.append(f"profit to loss: {swing['status']}")
    if swing["value"] is not None or swing["display"] is not None:
        failures.append(f"profit to loss produced a number: {swing['display']!r}")
    if not swing["render_absolute"]:
        failures.append("profit to loss did not ask for an absolute rendering")
    back = net_income_yoy(700, -300)
    if back["status"] != SIGN_CHANGE:
        failures.append(f"loss to profit: {back['status']}")
    both_negative = net_income_yoy(-700, -300)
    if both_negative["status"] != OK:
        failures.append("two losses are comparable and were refused")
    # Revenue is not sign-aware: negative revenue is a data problem, not a swing, and it
    # still must not produce a flattering percentage by accident.
    negative_revenue = revenue_yoy(-100, 1000)
    if negative_revenue["status"] != OK or direction(negative_revenue["value"]) != "turun":
        failures.append("negative revenue stopped reading as a fall")
    return failures, 6


def check_rounding_boundary():
    """Direction is computed unrounded. This is the case that proves it."""
    failures = []
    # +0,049% — rounds to "0,0%" at one decimal, but it is a rise.
    tiny = revenue_yoy(1000.49, 1000)
    if tiny["display"] != "0,0%":
        failures.append(f"the rounding boundary display moved: {tiny['display']}")
    if direction(tiny["value"]) != "naik":
        failures.append("a rise that rounds to zero was rounded into 'datar' — "
                        "direction is being computed on the display value")
    negative_tiny = revenue_yoy(999.51, 1000)
    if direction(negative_tiny["value"]) != "turun":
        failures.append("a fall that rounds to zero was rounded into 'datar'")
    if direction(0) != "datar" or direction(-0.0) != "datar":
        failures.append("exact zero, or negative zero, did not read as datar")
    if round_display(0.1234) != "12,3%":
        failures.append(f"the decimal separator is not a comma: {round_display(0.1234)}")
    return failures, 6


def check_unavailable():
    """A comparator that was never fetched is `unknown`, and says so differently."""
    failures = []
    result = unavailable("revenue_yoy", "yoy", "comparator_unavailable",
                         {"current": 8e12, "prior": None})
    if result["status"] != UNKNOWN or result["reason_code"] != "comparator_unavailable":
        failures.append(f"unavailable(): {result['status']} {result['reason_code']}")
    if result["display"] is not None:
        failures.append("an unavailable comparator rendered something")
    if result["formula"] != FORMULA["revenue_yoy"]:
        failures.append("an unavailable metric lost its formula")
    return failures, 3


def main():
    results = [("normal, real vectors", *check_normal()),
               ("null and zero", *check_missing_and_zero()),
               ("sign change", *check_sign_change()),
               ("rounding boundary", *check_rounding_boundary()),
               ("comparator absent", *check_unavailable())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nno unknown ever rendered a percentage" if not failed
          else f"\n{failed} metric failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
