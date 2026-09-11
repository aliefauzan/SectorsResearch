#!/usr/bin/env python3
"""
Rupiah as written numerals, and the parser that reads them back.

Pure: no I/O, no imports beyond the standard library. It exists in this folder rather
than being borrowed from `src/tunanetra/money.py` because that module answers a different
question — it spells numbers as *words* for a screen reader ("delapan triliun rupiah").
A carousel slide is read with the eyes, so it wants numerals. The scale ladder is the
same one, kept in the same order for the same reason: the largest match wins.

    from money import rupiah, exact_rupiah, magnitudes

    rupiah(8_004_471_444_300)          -> "Rp8,00 T"
    exact_rupiah(8_004_471_444_300)    -> "Rp8.004.471.444.300"
    magnitudes("naik ke Rp8,00 T")     -> [8004471444300.0]

The parser is the load-bearing half. `gate.py` compares the numbers a claim *says*
against the facts it *cites*, and a comparison done on strings would pass "Rp8,00 T"
against "Rp9,00 T" the moment either side reformatted. Both sides are parsed to a
magnitude and compared as numbers.

Indonesian convention throughout: `.` groups thousands, `,` is the decimal separator.
Getting that backwards turns 8,00 into eight hundred.

    python3 money.py      # every scale step, both directions, and the round trip
"""
import re

#: The Indonesian scale ladder, largest first — same values and same ordering rule as
#: `src/tunanetra/money.py:34`. The suffixes are the short written forms.
SCALES = (
    (1_000_000_000_000, "T", "triliun"),
    (1_000_000_000, "M", "miliar"),
    (1_000_000, "Jt", "juta"),
    (1_000, "Rb", "ribu"),
)

#: Suffix -> multiplier, for the parser. Long forms are accepted too, because a caption
#: written by hand in the review queue may well say "triliun".
MULTIPLIER = {}
for _value, _short, _long in SCALES:
    MULTIPLIER[_short.lower()] = _value
    MULTIPLIER[_long] = _value

PLACES = 2


def group(number):
    """`8004471444300` -> `"8.004.471.444.300"`. Thousands with dots, Indonesian style."""
    return f"{int(number):,}".replace(",", ".")


def decimal(value, places=PLACES):
    """`8.004…` -> `"8,00"`. Comma decimal separator, fixed places, no grouping."""
    return f"{float(value):.{places}f}".replace(".", ",")


def scale_of(value):
    """The largest scale step that fits, as `(divisor, short, long)`, or None."""
    magnitude = abs(float(value))
    for step, short, long_form in SCALES:
        if magnitude >= step:
            return step, short, long_form
    return None


def rupiah(value, places=PLACES, long_form=False):
    """A figure at its natural scale: `"Rp8,00 T"`, or `"Rp8,00 triliun"`."""
    if value is None:
        return None
    step = scale_of(value)
    if step is None:
        return f"Rp{group(round(float(value)))}"
    divisor, short, long_name = step
    suffix = long_name if long_form else short
    return f"Rp{decimal(float(value) / divisor, places)} {suffix}"


def exact_rupiah(value):
    """Every digit, for the evidence drawer: `"Rp8.004.471.444.300"`."""
    if value is None:
        return None
    return f"Rp{group(round(float(value)))}"


def signed_rupiah(value, places=PLACES):
    """A magnitude with its sign spelled out as a word, for a sign-change sentence."""
    if value is None:
        return None
    body = rupiah(abs(float(value)), places)
    return body if float(value) >= 0 else f"minus {body}"


#: A number in a sentence: optional `Rp`, digits grouped with dots, optional comma
#: decimals, optional scale suffix. Anchored on a word boundary so `q1-2026` and a bare
#: year are not read as money.
_NUMBER = re.compile(
    # The hyphen in the lookbehind is what keeps `q1-2026` from being read as the
    # number -2026: a minus sign directly after a word character is a hyphen.
    r"(?<![\w,.\-])"
    r"(?:Rp\s?)?"
    r"(-?\d{1,3}(?:\.\d{3})+|-?\d+)"            # 8.004.471.444.300 or 8
    r"(?:,(\d+))?"                              # ,00
    r"\s*(T|M|Jt|Rb|triliun|miliar|juta|ribu)?" # scale
    # `(?!\w)` and not `(?![\w.])`: a full stop at the end of a sentence is not part of
    # the number, and blocking on it silently dropped the scale suffix from "Rp8,00 T.".
    r"(?!\w)",
    re.IGNORECASE)


#: Things that contain digits and are not sums of money. Each is masked out before the
#: number scanner runs, because each one has its own check elsewhere: a period key is
#: checked by `gate.period_mismatch`, an endpoint is provenance, and a date is neither.
MASKED = (
    re.compile(r"/v2/[^\s,;]*"),                                   # /v2/…?n_quarters=8
    re.compile(r"\bq[1-4]-\d{4}\b", re.IGNORECASE),               # q1-2026
    re.compile(r"\bQ[1-4]\s+\d{4}\b", re.IGNORECASE),             # Q1 2026
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),                        # 2026-03-31
    re.compile(r"\b\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|"
               r"September|Oktober|November|Desember)\s+\d{4}\b"),  # 31 Maret 2026
)

#: A difference in percentage points is not a sum of money either, and it is checked
#: against the metric value rather than against a fact.
_POINTS = re.compile(r"(-?\d+(?:,\d+)?)\s*poin persentase", re.IGNORECASE)


def mask(text):
    """Blank out every non-monetary run of digits, keeping the string the same length."""
    out = text or ""
    for pattern in MASKED + (_POINTS,):
        out = pattern.sub(lambda m: " " * len(m.group(0)), out)
    return out


def points(text):
    """Every percentage-point figure in a string, as a fraction: `"1,2 poin"` -> 0.012."""
    return [float(m.group(1).replace(",", ".")) / 100.0 for m in _POINTS.finditer(text or "")]


def magnitudes(text):
    """Every number in a string, as a float magnitude. Percentages are left out.

    A percentage is not a magnitude and comparing one against a rupiah fact is a category
    error, so `"naik 12,3%"` yields nothing here — `gate.py` checks percentages against
    the metric display instead. `mask()` removes period keys, dates and endpoint paths
    for the same reason: they contain digits and are not sums of money.
    """
    out = []
    scanned = mask(text)
    for match in _NUMBER.finditer(scanned):
        whole, fraction, suffix = match.group(1), match.group(2), match.group(3)
        # Skip anything immediately followed by a percent sign: it is a rate, not a sum.
        tail = scanned[match.end():match.end() + 1]
        if tail == "%":
            continue
        digits = whole.replace(".", "")
        value = float(f"{digits}.{fraction}") if fraction else float(digits)
        if suffix:
            value *= MULTIPLIER[suffix.lower()]
        out.append(value)
    return out


def percentages(text):
    """Every percentage in a string, as a fraction: `"12,3%"` -> `0.123`."""
    out = []
    for match in re.finditer(r"(-?\d+(?:,\d+)?)\s*%", text or ""):
        out.append(float(match.group(1).replace(",", ".")) / 100.0)
    return out


def close_enough(first, second, tolerance=0.005):
    """Two magnitudes agree if they agree to within the display precision.

    `"Rp8,00 T"` is 8.00e12 read back, while the fact is 8_004_471_444_300 — the same
    number to the precision the slide actually showed. A tolerance of half a percent is
    wider than two decimal places at any scale step and narrower than any real error.
    """
    if first is None or second is None:
        return False
    first, second = float(first), float(second)
    if first == second:
        return True
    scale = max(abs(first), abs(second))
    return scale > 0 and abs(first - second) / scale <= tolerance


def close_rate(first, second, places=1):
    """Two rates agree if they agree to the precision a rate is DISPLAYED at.

    Rates are compared absolutely, not relatively: a margin of 6,2% is displayed to one
    decimal place, so anything within half a display step (0,05 percentage points) is the
    same number. The relative test in `close_enough` is far too tight down there — it
    would call 6,2% and 6,247% different — and far too loose up at 34%.
    """
    if first is None or second is None:
        return False
    half_step = 0.5 * (10 ** -places) / 100.0
    return abs(float(first) - float(second)) <= half_step + 1e-12


# ------------------------------------------------------------------------------ gates


def check_formatting():
    """Every scale step, and the Indonesian separators in the right places."""
    failures = []
    cases = [
        (8_004_471_444_300, "Rp8,00 T"),
        (28_677_339_000_000, "Rp28,68 T"),
        (2_178_080_414_220, "Rp2,18 T"),
        (999_000_000_000, "Rp999,00 M"),
        (1_500_000, "Rp1,50 Jt"),
        (2_500, "Rp2,50 Rb"),
        (999, "Rp999"),
        (0, "Rp0"),
        (-8_004_471_444_300, "Rp-8,00 T"),
    ]
    for value, expected in cases:
        got = rupiah(value)
        if got != expected:
            failures.append(f"rupiah({value}) = {got}, expected {expected}")
    if exact_rupiah(8_004_471_444_300) != "Rp8.004.471.444.300":
        failures.append(f"exact_rupiah: {exact_rupiah(8_004_471_444_300)}")
    if decimal(8.004) != "8,00":
        failures.append(f"the decimal separator is not a comma: {decimal(8.004)}")
    if rupiah(None) is not None or exact_rupiah(None) is not None:
        failures.append("a missing value was formatted into something")
    if signed_rupiah(-500_000_000_000) != "minus Rp500,00 M":
        failures.append(f"signed_rupiah: {signed_rupiah(-500_000_000_000)}")
    if rupiah(8_004_471_444_300, long_form=True) != "Rp8,00 triliun":
        failures.append("the long scale word is wrong")
    return failures, len(cases) + 5


def check_parsing():
    """The parser is what `gate.py` compares with. It must read every form back."""
    failures = []
    cases = [
        ("Pendapatan Rp8,00 T", [8.0e12]),
        ("Rp8.004.471.444.300", [8004471444300.0]),
        ("naik ke 28,68 T dari 28,43 T", [28.68e12, 28.43e12]),
        ("laba Rp2,18 triliun", [2.18e12]),
        ("Rp1,50 Jt dan Rp2,50 Rb", [1.5e6, 2500.0]),
        ("tumbuh 12,3%", []),                     # a rate is not a magnitude
        ("kuartal q1-2026", []),                  # a period key is not money
        ("Pendapatan Q1 2026 Rp8,00 T.", [8.0e12]),   # a trailing full stop, and a label
        ("Tanggal akhir periode 31 Maret 2026.", []),
        ("Periode 2026-03-31.", []),
        ("lihat /v2/financials/quarterly/ADRO/?n_quarters=8 untuk itu", []),
        ("Naik 0,6 poin persentase.", []),
        ("", []),
        (None, []),
    ]
    for text, expected in cases:
        got = magnitudes(text)
        if len(got) != len(expected) or any(not close_enough(a, b)
                                            for a, b in zip(got, expected)):
            failures.append(f"magnitudes({text!r}) = {got}, expected {expected}")

    read = percentages("tumbuh 12,3% dan turun -0,5%")
    if len(read) != 2 or not close_enough(read[0], 0.123) or not close_enough(read[1], -0.005):
        failures.append(f"percentages: {read}")
    if percentages("Rp8,00 T"):
        failures.append("a rupiah figure was read as a percentage")
    read_points = points("Naik 0,6 poin persentase dibanding Q4 2025.")
    if len(read_points) != 1 or not close_enough(read_points[0], 0.006):
        failures.append(f"points: {read_points}")
    if mask("Rp8,00 T pada q1-2026").strip() != "Rp8,00 T pada":
        failures.append(f"mask() removed the wrong thing: {mask('Rp8,00 T pada q1-2026')!r}")
    # A displayed rate must match the value it was rounded from, at both ends of the
    # scale — this is the comparison `gate.py` makes on every percentage on a slide.
    if not close_rate(-0.062, -0.06246508635570822):
        failures.append("a rate did not match the value it was displayed from")
    if not close_rate(0.341, 0.34057301440367627):
        failures.append("a large rate did not match the value it was displayed from")
    if close_rate(0.062, 0.075):
        failures.append("6,2% and 7,5% compared equal — the rate tolerance is too wide")
    return failures, len(cases) + 7


def check_round_trip():
    """What is printed must parse back to what it was printed from, within precision."""
    failures = []
    values = [8_004_471_444_300, 28_677_339_000_000, 2_178_080_414_220,
              14_861_321_000_000, 999_000_000_000, 1_500_000, 2_500]
    for value in values:
        parsed = magnitudes(rupiah(value))
        if len(parsed) != 1 or not close_enough(parsed[0], value):
            failures.append(f"{value} printed as {rupiah(value)} parsed back as {parsed}")
        exact = magnitudes(exact_rupiah(value))
        if len(exact) != 1 or exact[0] != float(value):
            failures.append(f"{value}: the exact form did not round-trip: {exact}")
    if close_enough(8.0e12, 9.0e12):
        failures.append("8,00 T and 9,00 T compared equal — the tolerance is too wide")
    if not close_enough(8.0e12, 8_004_471_444_300):
        failures.append("a displayed figure did not match the fact it was rounded from")
    return failures, len(values) + 2


def main():
    results = [("formatting", *check_formatting()),
               ("parsing", *check_parsing()),
               ("round trip", *check_round_trip())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nwhat is printed parses back to what it was printed from" if not failed
          else f"\n{failed} formatting failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
