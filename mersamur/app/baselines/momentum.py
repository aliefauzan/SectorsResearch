"""Baseline momentum — the opponent `riset/red-team.md` §A1 names by hand.

§A1 calls the momentum tautology the deepest flaw in the whole idea. IDX
cooling-down halts are triggered by a **mechanical rule** over cumulative price
increase, so "this stock will be halted" can collapse into "this stock has gone up
a lot and will go up more". The question a judge asks is quoted verbatim there:

    "Apa bedanya model empat sumbu kalian dengan mengurutkan saham berdasarkan
    kenaikan lima hari terakhir?"

This module *is* that sort. It ranks the universe by cumulative five-session gain
and warns the top five. Nothing else: no percentile, no distribution, no
threshold document, no cohort factor.

**Why the raw percentage here when `app.axes.momentum` refuses to use it.** The
axis reports a percentile precisely because a raw 20% five-session gain is
unremarkable in this tier (`riset/temuan-kelayakan.md` §Q3: median five-session
gain 23,8% for LIFE, 25,0% for SAFE). That refusal is a modelling decision, and a
baseline exists to test whether the decision bought anything. So the baseline gets
the naive quantity on purpose. If sorting by the raw number does as well as the
four axes, the percentile — and the other three axes with it — earned nothing.

**Same field as every other contender**, the same three ways
`previously_suspended` enforces:

1. *Same universe.* `run()` returns one `Prediction` per member, including the
   fifteen it does not warn. A baseline scored only over its own five names has a
   different denominator and would look better for it.
2. *Same sessions.* The series comes from `app.axes.volume_anomaly.series` and the
   windows from `app.axes.momentum.windows` — the same two functions the axis
   itself calls. The contest is over what is done with the sessions, so the
   sessions must not differ.
3. *Same record shape.* `Prediction` carries `(symbol, cutoff, warned, …)` exactly
   as `previously_suspended.Prediction` does, so `app.evaluate` scores all three
   contenders through one function.

**A ranking rule, not a per-symbol rule.** "Top five" is undefined for a single
symbol, so `run()` is the primitive here and there is no `predict()`. That is a
real difference from the other baseline and it is the reason the universe is a
required part of the call rather than an afterthought.

`warned` is a baseline's mechanical output for an offline comparison. It is not
product output and never reaches a reader.

Zero credits: reads only `research/harness/recorded/`, through the same accessor
the axis uses. No socket is opened.
"""
from dataclasses import dataclass, replace

from app import universe
from app.axes import momentum as momentum_axis
from app.axes.volume_anomaly import NoDailyDataError, series

NAME = "momentum_5h"

# Five sessions and five names, both taken from §A1's own sentence ("lima besar
# kenaikan kumulatif 5 hari") rather than chosen here. Neither is read from
# `state/thresholds.json`: a baseline that moves with the system it is measuring
# against stops being a fixed yardstick, and `tasks/11` forbids tuning either side
# of this comparison.
WINDOW = momentum_axis.WINDOW
TOP_N = 5


@dataclass(frozen=True)
class Prediction:
    """One symbol's baseline call at one cutoff, warned or not.

    `gain` is the cumulative return of the last `WINDOW` sessions and `rank` is 1
    for the strongest. Both are carried so a disagreement with the four-axis
    system can be read rather than guessed at.

    `rankable` is False when the series holds no usable window at all, or when it
    is all-zero: a halted stock's closes are carried forward, so it shows a flat
    0% run that is an artefact of the halt and not a measurement. Such a symbol
    stays in the universe — it is part of the denominator every contender is
    scored against — but it cannot be ranked and is never warned.
    """

    symbol: str
    cutoff: str
    warned: bool
    gain: float = None
    rank: int = None
    rankable: bool = True
    all_zero: bool = False
    window_start: str = ""
    window_end: str = ""
    n_sessions: int = 0
    note: str = ""

    @property
    def baseline(self):
        return NAME


def latest_gain(symbol, cache=None, start=None, end=None, window=WINDOW):
    """The most recent `window`-session cumulative return, and its dates.

    Returns `(gain, window_start, window_end, n_sessions, all_zero)`, with `gain`
    None when the series carries no complete window. Delegates the window
    arithmetic to `app.axes.momentum.windows` so the baseline and the axis cannot
    disagree about which sessions a five-session run spans, or about what a
    holiday inside it does.
    """
    data = series(symbol, cache=cache, start=start, end=end)
    rolling = momentum_axis.windows(data.sessions, size=window)
    latest = rolling[-1] if rolling else None
    return (latest.gain if latest else None,
            latest.start if latest else "",
            latest.end if latest else "",
            len(data),
            data.all_zero)


def run(cutoff, symbols=None, size=universe.DEFAULT_SIZE, cache=None,
        top_n=TOP_N, window=WINDOW, start=None, end=None):
    """A prediction for **every** member of the universe, strongest run first.

    `symbols=None` means the working universe the four-axis system screens.
    Passing an explicit list is for tests and for `app.evaluate`'s own basket; it
    is not a way to quietly narrow the field.

    `cutoff` is carried, not applied: the daily window is bounded by `start`/`end`
    (or by whatever window the recording holds), and the series accessor cannot
    reach past its own payload. It is recorded on every `Prediction` so a row from
    this baseline and a row from `previously_suspended` state the same as-of date.

    Ties are broken by symbol, ascending. That is arbitrary but fixed, so a rerun
    warns the same five names.
    """
    names = list(symbols) if symbols is not None else universe.watchlist(
        size=size, cache=cache)

    measured = []
    for name in names:
        want = universe.normalize(name)
        try:
            gain, w_start, w_end, n_sessions, all_zero = latest_gain(
                want, cache=cache, start=start, end=end, window=window)
        except (NoDailyDataError, ValueError, LookupError) as exc:
            measured.append(Prediction(symbol=want, cutoff=str(cutoff), warned=False,
                                       rankable=False,
                                       note=f"deret harian tidak terbaca: {exc}"))
            continue
        if gain is None:
            measured.append(Prediction(
                symbol=want, cutoff=str(cutoff), warned=False, rankable=False,
                n_sessions=n_sessions, all_zero=all_zero,
                note=f"kurang dari {window + 1} penutupan: tidak ada jendela penuh"))
            continue
        measured.append(Prediction(
            symbol=want, cutoff=str(cutoff), warned=False, gain=gain,
            rankable=not all_zero, all_zero=all_zero,
            window_start=w_start, window_end=w_end, n_sessions=n_sessions,
            note=("deret nol seluruhnya: kenaikan 0% adalah harga yang dibawa turun "
                  "dari sesi terakhir sebelum berhenti, bukan pergerakan"
                  if all_zero else "")))

    rankable = sorted((p for p in measured if p.rankable),
                      key=lambda p: (-p.gain, p.symbol))
    ranks = {p.symbol: i + 1 for i, p in enumerate(rankable)}
    top = {p.symbol for p in rankable[:max(top_n, 0)]}

    # Rebuilt in the caller's order, not in rank order: the evaluation set is the
    # universe as given, and reordering it here would let a reader mistake the
    # top of the list for the whole of it.
    return tuple(replace(p, rank=ranks.get(p.symbol), warned=p.symbol in top)
                 for p in measured)


def warned(predictions):
    """Only the symbols the rule fired on — a view, never the evaluation set."""
    return tuple(p for p in predictions if p.warned)


# --- description ------------------------------------------------------------
def _id(value):
    """Format a number the Indonesian way: comma as the decimal separator."""
    return str(value).replace(".", ",")


def _pct(value):
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return sign + _id("%.1f" % (value * 100)) + "%"


def describe(predictions, top_n=TOP_N):
    """A descriptive account of what the baseline would have flagged. No verdict."""
    if not predictions:
        return f"Baseline {NAME}: universe kosong — tidak ada yang bisa diurutkan."

    hits = warned(predictions)
    cutoff = predictions[0].cutoff
    ranked = [p for p in predictions if p.rankable and p.gain is not None]
    unranked = [p for p in predictions if not p.rankable]
    window = next((p for p in ranked if p.window_start), None)

    lines = [
        f"Baseline {NAME} — lawan tanding, per {cutoff} (0 kredit, dari rekaman)",
        f"  aturan           : urutkan kenaikan kumulatif {WINDOW} sesi, "
        f"peringatkan {top_n} teratas",
        f"  universe         : {len(predictions)} emiten — sama persis dengan yang "
        f"di-screen sistem utama",
        f"  bisa diurutkan   : {len(ranked)}"
        + (f" ({len(unranked)} tidak: deret nol atau tanpa jendela penuh)"
           if unranked else ""),
    ]
    if window:
        lines.append(f"  jendela terakhir : {window.window_start} .. {window.window_end}")
    lines.append(f"  diperingatkan    : {len(hits)}")
    for p in sorted(hits, key=lambda p: p.rank or 0):
        lines.append(f"    {p.rank}. {p.symbol:<5} {_pct(p.gain)}")
    if ranked:
        lines.append(f"  sebaran kenaikan : {_pct(min(p.gain for p in ranked))} .. "
                     f"{_pct(max(p.gain for p in ranked))}")
    lines += [
        "  Kenaikan mentah dipakai di sini justru karena sumbu momentum menolaknya "
        "dan memakai persentil. Kalau urutan mentah ini sama baiknya, penolakan itu "
        "tidak membeli apa-apa.",
        "  Baseline ini tidak dipakai sebagai keluaran produk. Ia ada untuk "
        "dikalahkan, dan kalau ia menang itu dilaporkan (tugas 11).",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from datetime import date

    when = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    print(describe(run(when)))
