#!/usr/bin/env python3
"""
The card: one symbol, four pillars, every figure carrying the field it came from.

Rendering only. It may not compute anything — if a number is not in a `Figure` produced by
`pillars.py`, it cannot appear here, and the gate at the bottom is what enforces that.

    ./run.sh pilar BBCA 2026-08-14

The last two blocks are the ones that make the card trustworthy rather than confident:
**YANG BELUM KAMI PERIKSA** names what the agent did not look at, and **FIELD** prints the
endpoints and fields behind every figure above, so a judge can re-derive any of them.
"""
import sys

import pillars as P
import sources
import thresholds as T

MARK = {P.TENANG: "·", P.WASPADA: "!", P.BAHAYA: "!!", P.TAK_TERUKUR: "?"}
WIDTH = 76


def _rule(char="─"):
    return char * WIDTH


def _wrap(text, indent=3, width=WIDTH):
    words, lines, line = text.split(), [], ""
    for word in words:
        if len(line) + len(word) + 1 > width - indent:
            lines.append(" " * indent + line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(" " * indent + line)
    return lines


def _number(figure):
    value, unit = figure.value, figure.unit
    if value is None:
        return "—"
    if isinstance(value, dict):
        return ", ".join(f"{k} {v:.0%}" for k, v in sorted(value.items(), key=lambda kv: -kv[1]))
    if unit == "fraksi" or unit == "fraksi float":
        return f"{value:.2%}" if abs(value) < 0.1 else f"{value:.1%}"
    if unit == "IDR":
        return f"Rp{value:,.0f}"
    if unit == "lembar":
        return f"{value:,.0f}"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def render(result, source, company=None):
    """The whole card as one string. Pure: it reads `result`, nothing else."""
    out = [_rule("━")]
    head = f"{result['verdict']}"
    if result["modifiers"]:
        head += "  ·  " + "  ·  ".join(result["modifiers"])
    out.append(head)
    label = f"{result['symbol']}"
    if company:
        label += f" · {company}"
    span = f"{result['window'][0]}..{result['window'][-1]}" if result["window"] else "—"
    out.append(f"{label}{' ' * max(1, WIDTH - len(label) - len(span) - len(source) - 5)}"
               f"{span} · {source}")
    out.append(_rule())

    for pillar in result["pillars"]:
        out.append(f"{MARK.get(pillar.status, '?'):>2} {pillar.name.upper()}  "
                   f"[{pillar.status}]")
        out += _wrap(pillar.headline)
        numbers = [f"{f.name} {_number(f)}" for f in pillar.figures if f.value is not None]
        if numbers:
            out += _wrap(" · ".join(numbers), indent=3)
        for figure in pillar.figures:
            if figure.note:
                out += _wrap(f"({figure.name}: {figure.note})", indent=5)
        out.append("")

    unchecked = [note for pillar in result["pillars"] for note in pillar.unchecked]
    if unchecked:
        out.append("   YANG BELUM KAMI PERIKSA")
        for note in unchecked:
            out += _wrap(f"— {note}", indent=5)
        out.append("")

    out.append("   FIELD")
    seen = []
    for pillar in result["pillars"]:
        for figure in pillar.figures:
            entry = (figure.endpoint, figure.fields)
            if entry not in seen:
                seen.append(entry)
    for endpoint, fields in seen:
        out += _wrap(f"{endpoint} → {', '.join(fields)}", indent=5)

    out.append("")
    out += _wrap("KATALIS menyatakan struktur transaksi, bukan nasihat investasi. "
                 "Tidak ada baris di atas yang berarti beli atau jual.", indent=3)
    out.append(_rule("━"))
    return "\n".join(out)


def method():
    """Every threshold the verdict turns on, and whether it shipped or was learned."""
    lines = ["AMBANG YANG BERLAKU", _rule()]
    width = max(len(name) for name in T.TABLE)
    for name in T.TABLE:
        origin, value = T.provenance(name)
        _, low, high, why = T.TABLE[name]
        lines.append(f"{name:<{width}}  {value:<8} [{low}, {high}]  {origin}")
        lines += _wrap(why, indent=2)
    lines.append("")
    lines.append("ALASAN SEBUAH SIMBOL DITOLAK")
    for reason, text in T.REJECTS.items():
        lines.append(f"  {reason:<16} {text}")
    return "\n".join(lines)


def show(symbol, as_of=None, source="recorded"):
    """Read locally, assess, print. Returns the exit code the CLI should use."""
    rows = sources.daily(source, symbol)
    if not rows:
        print(f"{symbol}: tidak ada deret harga di sumber {source}", file=sys.stderr)
        return 1
    as_of = as_of or rows[-1]["date"]
    try:
        result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
    except P.Rejected as exc:
        print(f"{sources.bare(symbol)} {as_of}: TIDAK DINILAI — {exc}")
        print(f"  alasan terdaftar: {T.REJECTS.get(exc.reason, 'tidak terdaftar')}")
        return 0
    print(render(result, source, company=sources.company_name(source, symbol)))
    return 0


# --------------------------------------------------------------------------------- gates

def check_every_number_is_a_figure():
    """No digit may reach the card that did not arrive inside a cited `Figure`.

    Rendering is where invented numbers get in, so the test is mechanical: take every run
    of digits in the card, and require each one to be traceable to a figure, a date, a
    threshold, or the symbol itself.
    """
    import re
    failures = []
    source, symbol, as_of = P.DEMO_CASES[0]
    result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
    text = render(result, source)

    # `\d+(?:[.,]\d+)*` keeps "1,234.56" whole while splitting "2026-09-02..2026-09-04"
    # into its parts, which a greedier pattern turns into the nonsense token "02..2026".
    number_like = r"\d+(?:[.,]\d+)*"
    allowed = set()
    for pillar in result["pillars"]:
        for figure in pillar.figures:
            allowed.add(figure.name)
            for text_source in (_number(figure), figure.note or "", figure.unit or ""):
                allowed.update(re.findall(number_like, text_source))
    for date in result["window"]:
        allowed.update(re.findall(r"\d+", date))
    allowed.update(re.findall(r"\d+", " ".join(str(v) for v in
                                               (T.get(n) for n in T.TABLE))))
    for pillar in result["pillars"]:
        allowed.update(re.findall(number_like, pillar.headline))
        for note in pillar.unchecked:
            allowed.update(re.findall(number_like, note))
    for token in re.findall(number_like, text):
        if token not in allowed:
            failures.append(f"number {token!r} on the card is not traceable to a figure")
    return failures, 1


def check_no_advice_in_render():
    failures = []
    source, symbol, as_of = P.DEMO_CASES[0]
    result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
    text = render(result, source).lower()
    for word in ("sebaiknya", "rekomendasi", "target harga", "layak beli", "jual sekarang"):
        if word in text:
            failures.append(f"advice phrase {word!r} reached the card")
    if "bukan nasihat investasi" not in text:
        failures.append("the card lost its no-advice line")
    return failures, 6


def check_field_block_is_complete():
    """Every endpoint a figure cites has to appear in the FIELD block."""
    failures = []
    source, symbol, as_of = P.DEMO_CASES[0]
    result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
    text = render(result, source)
    for pillar in result["pillars"]:
        for figure in pillar.figures:
            if figure.endpoint not in text:
                failures.append(f"{figure.endpoint} cited by {figure.name} but absent from FIELD")
    return failures, 1


def check_rejected_symbol_says_why():
    failures = []
    rows = sources.daily("recorded", "BBCA")
    early = rows[2]["date"]
    try:
        P.assess(P.bag_from("recorded", "BBCA", early), "BBCA", early)
        failures.append("a three-day series was scored instead of rejected")
    except P.Rejected as exc:
        if exc.reason not in T.REJECTS:
            failures.append(f"reject reason {exc.reason!r} is not in the threshold table")
    return failures, 1


def main():
    total, bad = 0, []
    for check in (check_every_number_is_a_figure, check_no_advice_in_render,
                  check_field_block_is_complete, check_rejected_symbol_says_why):
        failures, count = check()
        total += count
        bad += failures
        print(f"  {check.__name__:<34} {count - len(failures)}/{count}")
    for line in bad:
        print("FAIL", line)
    print(f"{total - len(bad)}/{total} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
