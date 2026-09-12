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
import re
import sys
from collections import Counter

import pillars as P
import sources
import thresholds as T

MARK = {P.TENANG: "·", P.WASPADA: "!", P.BAHAYA: "!!", P.TAK_TERUKUR: "?"}
WIDTH = 76

#: One run of digits, kept whole across "1,234.56" but split across "2026-09-02..2026-09-04",
#: which a greedier pattern turns into the nonsense token "02..2026". The renderer and its
#: gate must count with the same pattern or the comparison means nothing.
NUMBER = r"\d+(?:[.,]\d+)*"


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


def _render(result, source, company=None):
    """The card, and the multiset of number tokens this function itself emitted.

    Every line the card carries is appended through `put`, which counts the numbers in it as
    it goes. That counter — not a union of notes, units and headlines — is what the citation
    gate compares the finished card against. A number that reaches the card without passing
    through here changes the count, and a changed count is a red gate.
    """
    out, emitted = [], Counter()

    def put(*lines):
        for line in lines:
            out.append(line)
            emitted.update(re.findall(NUMBER, line))

    put(_rule("━"))
    head = f"{result['verdict']}"
    if result["modifiers"]:
        head += "  ·  " + "  ·  ".join(result["modifiers"])
    put(head)
    label = f"{result['symbol']}"
    if company:
        label += f" · {company}"
    span = f"{result['window'][0]}..{result['window'][-1]}" if result["window"] else "—"
    put(f"{label}{' ' * max(1, WIDTH - len(label) - len(span) - len(source) - 5)}"
        f"{span} · {source}")
    put(_rule())

    for pillar in result["pillars"]:
        put(f"{MARK.get(pillar.status, '?'):>2} {pillar.name.upper()}  "
            f"[{pillar.status}]")
        put(*_wrap(pillar.headline))
        numbers = [f"{f.name} {_number(f)}" for f in pillar.figures if f.value is not None]
        if numbers:
            put(*_wrap(" · ".join(numbers), indent=3))
        for figure in pillar.figures:
            if figure.note:
                put(*_wrap(f"({figure.name}: {figure.note})", indent=5))
        put("")

    unchecked = [note for pillar in result["pillars"] for note in pillar.unchecked]
    if unchecked:
        put("   YANG BELUM KAMI PERIKSA")
        for note in unchecked:
            put(*_wrap(f"— {note}", indent=5))
        put("")

    put("   FIELD")
    seen = []
    for figure in ([f for pillar in result["pillars"] for f in pillar.figures]
                   + list(result.get("modifier_figures") or [])):
        entry = (figure.endpoint, figure.fields)
        if entry not in seen:
            seen.append(entry)
    for endpoint, fields in seen:
        put(*_wrap(f"{endpoint} → {', '.join(fields)}", indent=5))

    put("")
    put(*_wrap("KATALIS menyatakan struktur transaksi, bukan nasihat investasi. "
               "Tidak ada baris di atas yang berarti beli atau jual.", indent=3))
    put(_rule("━"))
    return "\n".join(out), emitted


def render(result, source, company=None):
    """The whole card as one string. Pure: it reads `result`, nothing else."""
    return _render(result, source, company)[0]


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
    """No digit may reach the card that the renderer did not itself emit.

    The old form of this gate asked whether a token was a *member* of the union of every
    note, unit, headline and threshold on the card. That union is wide enough that invented
    numbers walked through it: `"rasio utang terhadap ekuitas 0.53, margin 2.32%"` scored
    green. The question here is narrower and is the right one — did `_render` write this
    number, and did it write it this many times.
    """
    failures = []
    for source, symbol, as_of in P.DEMO_CASES:
        result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
        _, emitted = _render(result, source)
        text = render(result, source)
        actual = Counter(re.findall(NUMBER, text))
        for token, count in sorted((actual - emitted).items()):
            failures.append(f"{symbol} {as_of}: number {token!r} appears {count} time(s) on "
                            f"the card without the renderer emitting it")
        for token, count in sorted((emitted - actual).items()):
            failures.append(f"{symbol} {as_of}: number {token!r} was emitted {count} more "
                            f"time(s) than the card shows — the card was rewritten")
    return failures, len(P.DEMO_CASES)


def check_no_advice_in_render():
    failures = []
    for source, symbol, as_of in P.DEMO_CASES:
        result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
        text = render(result, source).lower()
        for word in ("sebaiknya", "rekomendasi", "target harga", "layak beli", "jual sekarang"):
            if word in text:
                failures.append(f"{symbol}: advice phrase {word!r} reached the card")
        if "bukan nasihat investasi" not in text:
            failures.append(f"{symbol}: the card lost its no-advice line")
    return failures, 6 * len(P.DEMO_CASES)


def check_field_block_is_complete():
    """Every endpoint a figure cites has to appear in the FIELD block."""
    failures = []
    for source, symbol, as_of in P.DEMO_CASES:
        result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
        text = render(result, source)
        cited = ([f for pillar in result["pillars"] for f in pillar.figures]
                 + list(result.get("modifier_figures") or []))
        for figure in cited:
            if figure.endpoint not in text:
                failures.append(f"{symbol}: {figure.endpoint} cited by {figure.name} "
                                f"but absent from FIELD")
    return failures, len(P.DEMO_CASES)


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
