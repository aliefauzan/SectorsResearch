#!/usr/bin/env python3
"""
Numbers as Indonesian words, because a screen reader reads digits badly.

`1200000000000` is announced by NVDA and TalkBack as a run of digits or, at best, as
"one trillion two hundred billion" in the reader's own locale — which is English on most
Indonesian users' machines, since Indonesian TTS voices are patchy. Either way the
listener has to hold twelve digits in working memory to learn one fact. The fact is
"satu koma dua triliun rupiah", and that is what this module produces.

    from money import say_rupiah, say_percent, say_change

    say_rupiah(1_200_000_000_000)     -> "satu koma dua triliun rupiah"
    say_percent(0.2492)               -> "dua puluh empat koma sembilan persen"
    say_change(-0.0317)               -> "turun tiga koma dua persen"

Three rules, all of them about listening rather than reading:

  1. **Two significant figures after the scale word, never more.** "satu koma dua tiga
     empat triliun" is not more informative out loud, it is longer. The raw number is
     still on the page inside a `<table>` cell for anyone who wants every digit.
  2. **The scale word comes last.** Indonesian puts it there naturally, and it means the
     listener knows the magnitude at the end of a short phrase rather than after a long
     one.
  3. **Direction before magnitude for a change.** "turun tiga persen" is parseable the
     moment the first word lands; "tiga persen lebih rendah" is not.

Pure module: no I/O, no imports beyond the standard library, safe to unit test in
isolation.

    python3 money.py      # boundary cases at every scale step
"""

#: The Indonesian scale ladder. Order matters — the largest match wins.
SCALES = (
    (1_000_000_000_000, "triliun"),
    (1_000_000_000, "miliar"),
    (1_000_000, "juta"),
    (1_000, "ribu"),
)

UNITS = ("nol", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan",
         "sembilan")


def _spell_integer(number):
    """A whole number 0..999 as words. Above that the scale ladder takes over."""
    if number < 0:
        return "minus " + _spell_integer(-number)
    if number < 10:
        return UNITS[number]
    if number < 20:
        # 10..19 are irregular in Indonesian: belas, not "satu puluh".
        return {10: "sepuluh", 11: "sebelas"}.get(
            number, f"{UNITS[number - 10]} belas")
    if number < 100:
        tens, ones = divmod(number, 10)
        head = f"{UNITS[tens]} puluh"
        return head if not ones else f"{head} {UNITS[ones]}"
    if number < 1000:
        hundreds, rest = divmod(number, 100)
        head = "seratus" if hundreds == 1 else f"{UNITS[hundreds]} ratus"
        return head if not rest else f"{head} {_spell_integer(rest)}"
    raise ValueError("_spell_integer handles 0..999; the scale ladder handles the rest")


def _spell_decimal(value, places=1):
    """`1.2` -> "satu koma dua". Decimals are read digit by digit after `koma`.

    That is how Indonesian reads them, and it is also the unambiguous choice for a
    listener: "koma dua lima" cannot be confused with "koma dua puluh lima".
    """
    negative = value < 0
    value = abs(value)
    whole = int(value)
    fraction = round((value - whole) * (10 ** places))
    if fraction >= 10 ** places:                 # rounding carried into the whole part
        whole += 1
        fraction = 0
    words = _spell_integer(whole) if whole < 1000 else str(whole)
    if fraction:
        digits = str(fraction).rjust(places, "0").rstrip("0") or "0"
        words += " koma " + " ".join(UNITS[int(d)] for d in digits)
    return ("minus " + words) if negative else words


def say_number(value, places=1):
    """A bare number as words, with the Indonesian scale word where one applies."""
    if value is None:
        return "belum diambil"
    negative = value < 0
    magnitude = abs(value)
    for index, (size, name) in enumerate(SCALES):
        if magnitude < size:
            continue
        # Rounding can carry across a scale boundary: 999,999 is 999.999 ribu, which at
        # one decimal place is "1000 ribu" — a number no one says, and one that leaks
        # digits into speech. Promote it to the next scale word instead, so it reads
        # "satu juta". The raw figure is still in the table cell for anyone who wants
        # the last rupiah.
        if round(magnitude / size, places) >= 1000 and index:
            size, name = SCALES[index - 1]
        spoken = _spell_decimal(magnitude / size, places)
        return f"{'minus ' if negative else ''}{spoken} {name}"
    if magnitude == int(magnitude) and magnitude < 1000:
        return _spell_integer(int(value))
    return _spell_decimal(value, places)


def say_exact(value):
    """Every digit, spelled — for numbers where rounding destroys the fact.

    `say_number` exists to keep a twelve-digit market cap listenable, and rounding to two
    significant figures is right for that. It is wrong for a share price: rounding
    Rp6.350 to "enam ribu rupiah" and Rp6.700 to "tujuh ribu rupiah" turns a 5.5% move
    into a fabricated 17% one, and both endpoints of the move into numbers the exchange
    never printed. Prices, share counts under a million, and anything a listener might
    repeat back to a broker go through here instead.
    """
    if value is None:
        return "belum diambil"
    value = int(round(value))
    if value < 0:
        return "minus " + say_exact(-value)
    if value < 1000:
        return _spell_integer(value)
    for size, name in SCALES:
        if value >= size:
            head, rest = divmod(value, size)
            # "seribu", not "satu ribu" — Indonesian contracts the leading one at the
            # thousand step only.
            spoken = ("seribu" if head == 1 and name == "ribu"
                      else f"{say_exact(head)} {name}")
            return spoken if not rest else f"{spoken} {say_exact(rest)}"
    return _spell_integer(value)


def say_rupiah(value, places=1):
    """A rupiah amount, magnitude first and the currency last. Rounded — see `say_exact`."""
    if value is None:
        return "belum diambil"
    return f"{say_number(value, places)} rupiah"


def say_price(value):
    """A price level, every digit spelled. Never rounded."""
    if value is None:
        return "belum diambil"
    return f"{say_exact(value)} rupiah"


def say_shares(value, places=1):
    """A share count. Same ladder, different unit noun."""
    if value is None:
        return "belum diambil"
    return f"{say_number(value, places)} lembar"


def say_percent(fraction, places=1):
    """A fraction rendered as spoken percent. `0.2492` -> "dua puluh empat koma sembilan persen"."""
    if fraction is None:
        return "belum diambil"
    return f"{_spell_decimal(fraction * 100, places)} persen"


def say_change(fraction, places=1, up="naik", down="turun", flat="tidak berubah"):
    """A signed change, direction first.

    Direction leads because it is the part a listener can act on immediately. A change
    that rounds to zero at the requested precision reads as "tidak berubah" rather than
    as "naik nol persen", which sounds like a measurement rather than a non-event.
    """
    if fraction is None:
        return "belum diambil"
    magnitude = abs(fraction) * 100
    if round(magnitude, places) == 0:
        return flat
    word = up if fraction > 0 else down
    return f"{word} {_spell_decimal(magnitude, places)} persen"


def say_date(iso):
    """`2026-08-31` -> "31 Agustus 2026". Screen readers read ISO dates as three numbers."""
    if not iso:
        return "belum diambil"
    months = ("Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
              "Agustus", "September", "Oktober", "November", "Desember")
    try:
        year, month, day = (int(part) for part in iso.split("-")[:3])
        return f"{day} {months[month - 1]} {year}"
    except (ValueError, IndexError):
        return iso


def say_count(number, noun, plural=None):
    """`say_count(4, "bulan")` -> "empat bulan". Indonesian does not inflect for plural."""
    return f"{_spell_integer(number) if number < 1000 else number} {plural or noun}"


# ------------------------------------------------------------------------------ gates


def check_scale_ladder():
    """One case on each side of every scale boundary, where off-by-one lives."""
    failures = []
    cases = [
        (999, "sembilan ratus sembilan puluh sembilan"),
        (1_000, "satu ribu"),
        (1_500, "satu koma lima ribu"),
        # Rounds across the boundary: 999.999 ribu is "satu juta" out loud, not
        # "1000 ribu". The exact figure stays in the table.
        (999_999, "satu juta"),
        (999_400, "sembilan ratus sembilan puluh sembilan koma empat ribu"),
        (1_000_000, "satu juta"),
        (1_000_000_000, "satu miliar"),
        (1_000_000_000_000, "satu triliun"),
        (1_200_000_000_000, "satu koma dua triliun"),
        (-2_500_000_000, "minus dua koma lima miliar"),
        (0, "nol"),
    ]
    for value, expected in cases:
        got = say_number(value)
        if got != expected:
            failures.append(f"say_number({value}) = {got!r}, expected {expected!r}")
    return failures, len(cases)


def check_spelling():
    """The irregular decades, which are where an Indonesian speller usually breaks."""
    failures = []
    cases = [(10, "sepuluh"), (11, "sebelas"), (12, "dua belas"), (20, "dua puluh"),
             (21, "dua puluh satu"), (100, "seratus"), (101, "seratus satu"),
             (250, "dua ratus lima puluh"), (999, "sembilan ratus sembilan puluh sembilan")]
    for value, expected in cases:
        got = _spell_integer(value)
        if got != expected:
            failures.append(f"_spell_integer({value}) = {got!r}, expected {expected!r}")
    return failures, len(cases)


def check_exact():
    """Prices must survive intact. This is the gate that stops a rounded price level."""
    failures = []
    cases = [
        (6_350, "enam ribu tiga ratus lima puluh"),
        (6_700, "enam ribu tujuh ratus"),
        (1_000, "seribu"),
        (1_005, "seribu lima"),
        (105, "seratus lima"),
        (0, "nol"),
        (-250, "minus dua ratus lima puluh"),
        (1_234_567, "satu juta dua ratus tiga puluh empat ribu lima ratus enam puluh tujuh"),
    ]
    for value, expected in cases:
        got = say_exact(value)
        if got != expected:
            failures.append(f"say_exact({value}) = {got!r}, expected {expected!r}")
    if say_price(6_350) == say_price(6_700):
        failures.append("two different prices spoke identically — rounding is back")
    return failures, len(cases) + 1


def check_percent_and_change():
    """The two forms a sentence actually reaches for, including the rounding edges."""
    failures = []
    cases = [
        (say_percent(0.2492), "dua puluh empat koma sembilan persen"),
        (say_percent(0.75), "tujuh puluh lima persen"),
        (say_percent(0.0), "nol persen"),
        (say_change(0.0317), "naik tiga koma dua persen"),
        (say_change(-0.0317), "turun tiga koma dua persen"),
        (say_change(0.0001), "tidak berubah"),
        (say_change(None), "belum diambil"),
        (say_rupiah(None), "belum diambil"),
        (say_date("2026-08-31"), "31 Agustus 2026"),
        (say_count(4, "bulan"), "empat bulan"),
    ]
    for got, expected in cases:
        if got != expected:
            failures.append(f"got {got!r}, expected {expected!r}")
    return failures, len(cases)


def check_no_digits_leak():
    """Nothing a listener hears should contain a bare digit run below the scale ladder.

    Above a triliun the ladder runs out and a raw integer is the honest fallback, so the
    check is scoped to values the ladder covers.
    """
    failures = []
    for value in (0, 7, 99, 1_234, 56_780_000, 4_100_000_000, 8_900_000_000_000):
        spoken = say_rupiah(value)
        if any(character.isdigit() for character in spoken):
            failures.append(f"say_rupiah({value}) leaked digits: {spoken!r}")
    return failures, 7


def main():
    results = [("scale ladder", *check_scale_ladder()),
               ("integer spelling", *check_spelling()),
               ("exact spelling", *check_exact()),
               ("percent and change", *check_percent_and_change()),
               ("no digit leak", *check_no_digits_leak())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:20} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)

    print(f"\n{say_rupiah(1_200_000_000_000)} · {say_percent(0.2492)} · "
          f"{say_change(-0.0317)}" if not failed else f"\n{failed} spelling failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
