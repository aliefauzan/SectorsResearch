"""Suspension history turned into a dated, backtestable event set.

`/v2/suspensions/` is the product's only ground truth: 585 rows, 2018-12-28 to
2026-09-09, already paid for and sitting in `research/harness/recorded/`. This
module is the single place that reads them, and it enforces three rules that the
feasibility pass (`riset/temuan-kelayakan.md` §Q4) showed are not optional.

**One positive class.** Only `cooling_down` — the IDX price-surge halt — is a
label. The other eight classes (`going_concern`, `late_report`, `delisting`, …)
are kept, because they are real history and make good features, but they are a
different question and must never be scored as the target.

**One regime.** There are zero cooling-down suspensions before 2025: 53 pre-2025
rows, none of them the label class. The usable history is 20 months, not 7.7
years, and pre-2025 events are dropped from the label set rather than diluted
into it — including them would train across a rule change.

**One door onto the past.** 78% of cooling-down events come from symbols that
were suspended before, so a model can win by memorising a recidivist list. Any
module that wants suspension history as a *feature* must go through
`history_before(symbol, cutoff)`, which cannot return an event dated on or after
the cutoff. That is the whole point of it being the only accessor.

Zero credits: everything here reads the recording.
"""
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from datetime import date as _date   # alias: the Event field is also called `date`

from app.cache import Cache

# The call that holds the history. Slug: v2_suspensions__limit-30 (20 credits,
# 20 pages, merged) — already settled, so this never reaches the network.
SUSPENSIONS_PATH = "/v2/suspensions/"
SUSPENSIONS_PARAMS = {"limit": 30}

# Reason patterns, ordered — first match wins. Copied verbatim from
# `tools/feasibility.py`, which derived them from all 585 live rows; copied rather
# than imported because `tools/` is research scaffolding the product must not take
# a runtime dependency on. Do not "simplify" the first pattern: "dalam rangka
# cooling down" appears BOTH with and without the "peningkatan harga kumulatif"
# preamble, and matching only the preamble loses 17 events (435 instead of 452).
REASON_PATTERNS = [
    ("cooling_down",  r"peningkatan harga kumulatif|cooling down"),
    ("ppk_over_1y",   r"papan pemantauan khusus selama lebih dari"),
    ("price_decline", r"penurunan harga"),
    ("going_concern", r"kelangsungan usaha"),
    ("late_report",   r"belum menyampaikan laporan|belum melakukan pembayaran"),
    ("delisting",     r"delisting|buyback"),
    ("rule_I_A",      r"peraturan bursa nomor i-a|ketentuan v\.1\.1"),
    ("long_suspend",  r"suspend more than"),
]
# Nine classes: the eight above plus `other` for rows none of them match.
REASON_CLASSES = tuple(name for name, _ in REASON_PATTERNS) + ("other",)

LABEL_CLASS = "cooling_down"
# First day of the regime in which the label class exists at all.
REGIME_START = date(2025, 1, 1)
# IDX listed companies, order of magnitude. The denominator of the base rate; it
# is an estimate, which is why the rate is reported as approximate.
LISTED_UNIVERSE = 900


def classify(reason):
    """Map a free-text `reason` to one of the nine classes."""
    text = (reason or "").lower()
    for name, pattern in REASON_PATTERNS:
        if re.search(pattern, text):
            return name
    return "other"


def parse_date(text):
    """`YYYY-MM-DD` to a `date`, or None if the row carries no usable date."""
    try:
        y, m, d = (int(v) for v in str(text)[:10].split("-"))
        return date(y, m, d)
    except (ValueError, AttributeError):
        return None


@dataclass(frozen=True)
class Event:
    """One suspension announcement. Immutable so a caller cannot re-date it."""

    symbol: str          # bare ticker, ".JK" stripped
    date: _date
    reason_class: str
    reason: str
    pdf_url: str = ""

    @property
    def is_label(self):
        """True for events that may be used as a positive target."""
        return self.reason_class == LABEL_CLASS and self.date >= REGIME_START


_EVENTS = None


def load_events(cache=None, reload=False):
    """Every suspension on record, all classes and all years, sorted by date.

    Kept whole on purpose: the pre-2025 rows and the non-label classes are still
    true history and still legitimate *features*. It is the label set that is
    filtered, not the archive. `cache` is injectable so tests can build their own
    corpus instead of asserting against whatever the harness holds today.
    """
    global _EVENTS
    if cache is None and _EVENTS is not None and not reload:
        return _EVENTS

    # `cache if cache is not None` — NOT `cache or`: an empty Cache is falsy
    # (it defines __len__), so `or` would silently fall back to the real corpus.
    source = cache if cache is not None else Cache()
    hit = source.get(SUSPENSIONS_PATH, SUSPENSIONS_PARAMS)
    rows = []
    if hit is not None and hit.found:
        payload = hit.payload
        rows = payload.get("results") if isinstance(payload, dict) else payload
        rows = rows or []

    events = []
    for row in rows:
        when = parse_date(row.get("suspension_date"))
        if when is None:
            continue          # undated row: cannot be placed on a timeline at all
        reason = row.get("reason") or ""
        events.append(Event(
            symbol=(row.get("symbol") or "").replace(".JK", "").upper(),
            date=when,
            reason_class=classify(reason),
            reason=reason,
            pdf_url=row.get("pdf_url") or "",
        ))
    events.sort(key=lambda e: (e.date, e.symbol))

    if cache is None:
        _EVENTS = events
    return events


def events(symbol=None, before=None, after=None, reason_class=None, cache=None):
    """Dated events, optionally bounded in time, so a caller can force a horizon.

    `before` is **exclusive** and `after` is **inclusive**: `events(s,
    before=d)` is everything strictly earlier than `d`, which is the bound a
    backtest needs. All nine classes are returned unless `reason_class` narrows
    it; this is the archive view, not the label view.
    """
    out = load_events(cache=cache)
    if symbol:
        want = symbol.replace(".JK", "").upper()
        out = [e for e in out if e.symbol == want]
    if before is not None:
        out = [e for e in out if e.date < before]
    if after is not None:
        out = [e for e in out if e.date >= after]
    if reason_class is not None:
        out = [e for e in out if e.reason_class == reason_class]
    return out


def history_before(symbol, cutoff_date, cache=None):
    """Suspension history visible at `cutoff_date` — the only leak-safe accessor.

    Every other module must read past suspensions through this function. It can
    only ever return events dated strictly before the cutoff, so a feature built
    from it cannot contain the event it is meant to predict, nor anything that
    happened between the cutoff and that event. Pass the FIRST day of the feature
    window as the cutoff, not the event date: an event inside the window is still
    future information relative to the window's own start.

    All classes are included — a prior `going_concern` halt is real prior
    information — and pre-2025 events are included too, because as a feature
    (unlike as a label) old history is still something a reader knew at the time.
    """
    if cutoff_date is None:
        raise ValueError("history_before butuh cutoff_date; tanpa itu tidak ada batas kebocoran")
    return events(symbol=symbol, before=cutoff_date, cache=cache)


def label_events(cache=None):
    """The positive target set: `cooling_down` only, 2025 onward. 452 events."""
    return [e for e in load_events(cache=cache) if e.is_label]


def reason_counts(cache=None):
    """Events per reason class, over the whole archive. Matches §Q4's table."""
    return Counter(e.reason_class for e in load_events(cache=cache))


def counts_by_year(cache=None):
    """`{year: Counter(reason_class)}` — the shape that shows the regime break."""
    out = defaultdict(Counter)
    for e in load_events(cache=cache):
        out[e.date.year][e.reason_class] += 1
    return dict(out)


def base_rate(year, cache=None):
    """Cooling-down base rate for one regime year, per stock per 10 trading days.

    Returns `{year, events, trading_days, per_day, per_stock_10d}` or None when
    the year holds fewer than two label events to span.

    The trading-day span is the calendar span scaled by 5/7, which is what
    `tools/feasibility.py` used to produce the 0,77% in `temuan-kelayakan.md`;
    it is reproduced here so the product and the research note cannot disagree.
    It is an approximation — counting IDX trading days exactly for 2026 gives 159
    rather than ~174, and so a rate nearer 0,84%. Either way the number is small
    enough that bare precision will look bad for any model, which is why the
    product reports lift rather than accuracy.
    """
    cool = [e for e in label_events(cache=cache) if e.date.year == year]
    if len(cool) < 2:
        return None
    first, last = cool[0].date, cool[-1].date
    calendar_days = ((last.year - first.year) * 365
                     + (last.month - first.month) * 30
                     + (last.day - first.day))
    trading_days = max(calendar_days * 5 / 7, 1)
    per_day = len(cool) / trading_days
    return {
        "year": year,
        "events": len(cool),
        "trading_days": trading_days,
        "per_day": per_day,
        "per_stock_10d": per_day * 10 / LISTED_UNIVERSE,
    }


def base_rates(cache=None):
    """Base rate for every regime year that has one, oldest first."""
    years = sorted({e.date.year for e in label_events(cache=cache)})
    return [r for r in (base_rate(y, cache=cache) for y in years) if r]


def _id(value):
    """Format a number the Indonesian way: comma as the decimal separator."""
    return str(value).replace(".", ",")


def summary(cache=None):
    """A descriptive account of the label set. No verdict, no score, no signal."""
    labels = label_events(cache=cache)
    archive = load_events(cache=cache)
    symbols = Counter(e.symbol for e in labels)
    repeat_events = sum(n for n in symbols.values() if n > 1)
    kinds = reason_counts(cache=cache)
    dropped = [e for e in archive if e.date < REGIME_START]

    lines = [
        "Set label suspensi — dari /v2/suspensions/ yang sudah terekam (0 kredit)",
        f"  arsip            : {len(archive)} peristiwa, "
        f"{archive[0].date.isoformat()} .. {archive[-1].date.isoformat()}" if archive
        else "  arsip            : kosong",
    ]
    if not archive:
        return "\n".join(lines)

    lines += [
        f"  kelas positif    : {len(labels)} cooling-down "
        f"(sejak {REGIME_START.isoformat()}), {len(symbols)} emiten unik",
        "  berulang         : %d/%d peristiwa (%d%%) dari emiten yang pernah "
        "disuspensi sebelumnya"
        % (repeat_events, len(labels),
           round(repeat_events / max(len(labels), 1) * 100)),
        f"  dibuang pra-2025 : {len(dropped)} peristiwa, "
        f"{sum(1 for e in dropped if e.reason_class == LABEL_CLASS)} di antaranya cooling-down",
        "  kelas alasan     : " + ", ".join(
            f"{name} {kinds.get(name, 0)}" for name in REASON_CLASSES),
        "",
        f"  {'TAHUN':6}{'cooling':>9}{'lain':>7}{'TOTAL':>8}",
    ]
    for year, counter in sorted(counts_by_year(cache=cache).items()):
        cool = counter.get(LABEL_CLASS, 0)
        total = sum(counter.values())
        lines.append(f"  {year:<6}{cool:>9}{total - cool:>7}{total:>8}")

    lines.append("")
    for rate in base_rates(cache=cache):
        pct = _id("%.2f" % (rate["per_stock_10d"] * 100))
        per_day = _id("%.2f" % rate["per_day"])
        lines.append(
            "  base rate %d  : %s%% per saham per 10 hari bursa "
            "(%d peristiwa / ~%.0f hari bursa = %s per hari)"
            % (rate["year"], pct, rate["events"], rate["trading_days"], per_day))
    lines.append("  Angka ini deskriptif: seberapa jarang peristiwanya, bukan penilaian.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())
