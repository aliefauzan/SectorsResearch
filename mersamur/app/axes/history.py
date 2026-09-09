"""Sumbu riwayat — what was already on the record about this stock before the window.

This is the cheapest feature in the product and possibly the strongest, and that is
precisely why it is the most dangerous one. `riset/temuan-kelayakan.md` §Q4 finding 3:

    452 cooling-down events / 236 unique symbols = 1,92 per symbol
    353/452 (78%) belong to symbols that appear in the label set more than once

A model can score well on that by memorising a recidivist list and understanding
nothing. Two defences are built into this module, and neither is optional.

**One door onto the past.** Every read of suspension history here goes through
`labels.history_before(symbol, cutoff)`, which cannot return an event dated on or
after the cutoff. Nothing in this file opens the recording, imports `Cache`, or
calls any other `labels` accessor — `labels.events` and `labels.load_events` are
unbounded in time and would hand back the very event this axis is used to predict.
`tests/test_history.py` asserts that by parsing this file, not by trusting it.

**The 78% is a hindsight number, and the honest one is smaller.** 353/452 counts
every event of a repeat offender, including that symbol's *first* one — at which
point there was nothing to memorise. Measured the way a forecaster actually stands,
with `history_before(symbol, event_date)`, only **225 of 452 (50%)** of cooling-down
events had any visible prior suspension of any class. The gap between 78% and 50% is
exactly the leak this module refuses to take, so both numbers are reported rather
than the flattering one.

The features are three, and they are the three the task names: how many suspensions
stand before the cutoff, how long ago the most recent one was, and what classes they
belonged to. All nine reason classes count as history — a 2019 `late_report` halt is
real prior information about a company the exchange has already had to look at —
even though only `cooling_down` since 2025 may ever be a *label* (`app.labels`).

No threshold is read and nothing fires. `state/thresholds.json` carries no bar for
this axis, and inventing one here would be the hardcoded constant `app.axes` exists
to refuse. The pure "has ever been suspended" rule lives in
`app/baselines/previously_suspended.py`, where it is a competitor to be beaten
rather than a component to be scored.

Zero credits: `labels` reads a recording that was already paid for, and this module
never reaches past it.
"""
from dataclasses import dataclass
from datetime import date

from app import labels

AXIS = "history"

# The class that is also the product's label. Counted separately because "suspended
# three times for late filings" and "halted three times for a price surge" are
# different histories, and collapsing them would hide which one the reader has.
LABEL_CLASS = labels.LABEL_CLASS

# The nine class names, in the order `app.labels` defines them. A constant, not an
# accessor: reading it touches no event and no file.
REASON_CLASSES = labels.REASON_CLASSES


def as_date(value):
    """`date`, `"YYYY-MM-DD"`, or None -> `date` or None. No `labels` call.

    Deliberately local rather than borrowed from `labels.parse_date`: this module
    is allowed exactly one function from that module, and keeping it that way is
    what makes the leak rule checkable by reading the file.
    """
    if isinstance(value, date):
        return value
    try:
        y, m, d = (int(part) for part in str(value)[:10].split("-"))
        return date(y, m, d)
    except (ValueError, AttributeError, TypeError):
        return None


def prior_events(symbol, cutoff, cache=None):
    """Suspensions visible at `cutoff`, oldest first — the module's only data source.

    `cutoff` must be the **first day of the feature window**, not the event date:
    anything inside the window is still future information relative to the window's
    own start. A missing cutoff raises out of `labels.history_before` rather than
    defaulting to today, because a default here would silently be a leak.
    """
    when = as_date(cutoff)
    if when is None:
        raise ValueError(
            "Sumbu riwayat butuh cutoff bertanggal (date atau 'YYYY-MM-DD'); "
            "tanpa itu tidak ada batas kebocoran.")
    return tuple(labels.history_before(symbol, when, cache=cache))


@dataclass(frozen=True)
class History:
    """One symbol's suspension record as of a cutoff. Immutable — no re-dating.

    `days_since_last` is `None` when there is no prior event at all. Not 0, and not
    a large sentinel: "never suspended" is a different statement from "suspended
    today", and a number in that slot would let either be mistaken for the other.
    """

    symbol: str
    cutoff: str = ""
    n_prior: int = 0
    n_prior_label: int = 0
    days_since_last: int = None
    last_date: str = ""
    last_reason_class: str = ""
    first_date: str = ""
    reason_counts: tuple = ()

    @property
    def repeat(self):
        """True when anything at all stands before the cutoff. The baseline's rule."""
        return self.n_prior > 0

    @property
    def status(self):
        """`tanpa_riwayat` · `pernah_disuspensi` · `pernah_cooling_down`. Descriptive."""
        if self.n_prior == 0:
            return "tanpa_riwayat"
        if self.n_prior_label > 0:
            return "pernah_cooling_down"
        return "pernah_disuspensi"

    def __str__(self):
        return describe(self)


def score(symbol, cutoff, cache=None):
    """Measure the history axis for one symbol as of `cutoff`. Reads nothing else."""
    when = as_date(cutoff)
    found = prior_events(symbol, cutoff, cache=cache)

    counts = {}
    for event in found:
        counts[event.reason_class] = counts.get(event.reason_class, 0) + 1
    ordered = tuple((name, counts[name]) for name in REASON_CLASSES if name in counts)

    last = found[-1] if found else None
    return History(
        symbol=(symbol or "").replace(".JK", "").upper(),
        cutoff=when.isoformat() if when else "",
        n_prior=len(found),
        n_prior_label=counts.get(LABEL_CLASS, 0),
        # None, not 0: absence of history is not a recent halt.
        days_since_last=(when - last.date).days if last and when else None,
        last_date=last.date.isoformat() if last else "",
        last_reason_class=last.reason_class if last else "",
        first_date=found[0].date.isoformat() if found else "",
        reason_counts=ordered,
    )


# --- description ------------------------------------------------------------
def _id(value):
    """Format a number the Indonesian way: comma as the decimal separator."""
    return str(value).replace(".", ",")


def describe(result):
    """A descriptive account of one symbol's record. No verdict, no colour."""
    lines = [f"Riwayat {result.symbol} — suspensi sebelum {result.cutoff} "
             f"(0 kredit, dari rekaman)"]
    lines.append(f"  batas kebocoran  : peristiwa sejak {result.cutoff} tidak dihitung")

    if result.n_prior == 0:
        lines += [
            "  suspensi sebelumnya: tidak ada satu pun pada tanggal itu",
            "  jarak dari terakhir: tidak terukur — belum ada yang terakhir",
            f"  status           : {result.status}",
            "  Ini catatan bursa, bukan penilaian atas emitennya.",
        ]
        return "\n".join(lines)

    named = ", ".join(f"{name} {n}" for name, n in result.reason_counts)
    lines += [
        f"  suspensi sebelumnya: {result.n_prior} peristiwa, "
        f"{result.first_date} .. {result.last_date}",
        f"  di antaranya cooling-down: {result.n_prior_label}",
        f"  terakhir         : {result.last_date} "
        f"({result.last_reason_class}), {_id(result.days_since_last)} hari sebelum cutoff",
        f"  kelas alasan     : {named}",
        f"  status           : {result.status}",
        "  Angka ini deskriptif: apa yang sudah tercatat, bukan perkiraan apa yang "
        "akan terjadi maupun anjuran tindakan.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    cutoff = args[-1] if args and as_date(args[-1]) else date.today().isoformat()
    symbols = [a for a in args if not as_date(a)] or ["PACK"]
    for arg in symbols:
        print(score(arg, cutoff))
        print()
