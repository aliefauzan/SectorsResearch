"""Sumbu momentum — a five-session run expressed as a percentile of the stock itself.

The raw percentage is not the axis. **These stocks routinely move 13–29% in five
sessions on an ordinary week** (`riset/temuan-kelayakan.md` §Q3): the median
five-session gain is 23,8% for LIFE, 25,0% for SAFE, 21,4% for TRUK. A rule that
says "up 20% is notable" fires on half the universe every week and means nothing.
What is measurable is where *this* window sits in the distribution of every
five-session window that stock has produced — so the axis reports a percentile,
and the percentage is carried alongside only as context.

§Q3 is also the reason the axis is deliberately weak on its own. Across the ten
suspended names the pre-suspension window sat at a median percentile of 81 and only
2 of 12 events cleared 90. Momentum is a component of a profile, not a screen: if
it were sufficient the whole product would be `ORDER BY gain5 DESC`, and the note
shows it is not.

Two mechanical rules keep the distribution honest.

**Windows are counted in sessions, never in calendar days.** Five sessions across
the 17 August holiday still means five real trading dates and never a synthesised
empty day at a closed-market price. `crosses_holiday` marks such a window, because
it is the one case where the day-of-week composition of the window is unbalanced.

**Day-of-week seasonality cancels inside a window rather than being subtracted.**
A five-session window normally holds one Monday, one Tuesday and so on, so the
weekly shape is already netted out by construction — which is why de-seasonalising
here would remove a bias that is not present. It is volume, measured one session at
a time, that needs the correction (`volume_anomaly.weekday_factors`). The exception
is a window crossing a holiday, and that window says so.

Zero credits: reads only `research/harness/recorded/`, through
`volume_anomaly.series` so both axes see the same sessions and the same window
caveat. No socket is opened.
"""
import statistics
from dataclasses import dataclass

from app import axes, universe
from app.axes.volume_anomaly import (
    DEFAULT_WINDOW_SESSIONS,
    FULL_WINDOW_SESSIONS,
    NoDailyDataError,      # noqa: F401 — re-exported: callers catch one error type
    holidays_between,
    series,
    suspensions_in_window,
)

AXIS = "momentum"

# Five sessions: one trading week, and the horizon §Q3 measured.
WINDOW = 5

# A percentile computed over fewer windows than this is a rank out of a handful,
# not a distribution. The bare 21-session payload yields 16 windows, which is thin
# but usable and is exactly what the note's table was built on.
MIN_WINDOWS = 8


def percentile_of(values, value):
    """Share of `values` that `value` is greater than or equal to, in percent.

    The empirical CDF: `100 * #{v <= value} / N`, so the largest window in a series
    is percentile 100 by construction and the smallest is `100/N`. §Q3's table used
    the strictly-below variant instead, which caps the largest window at 94 out of
    16 windows — the same ordering, one convention apart. This one is used because
    "the highest window reads ~100" is the property the axis is checked against, and
    a percentile whose maximum is 94 invites the reader to wonder what the missing
    6 belongs to.
    """
    if not values:
        return None
    return 100.0 * sum(1 for v in values if v <= value) / len(values)


@dataclass(frozen=True)
class Window:
    """One five-session run. `dates` holds real trading dates only, never gaps."""

    dates: tuple = ()
    gain: float = 0.0
    holidays: tuple = ()

    @property
    def start(self):
        return self.dates[0].isoformat() if self.dates else ""

    @property
    def end(self):
        return self.dates[-1].isoformat() if self.dates else ""

    @property
    def crosses_holiday(self):
        """True when the exchange was closed on a weekday inside this window."""
        return bool(self.holidays)

    @property
    def sessions(self):
        return len(self.dates)


def windows(sessions, size=WINDOW):
    """Every rolling `size`-session window in a series, oldest first.

    The gain spans `size` sessions and therefore `size + 1` closes: the first close
    is the reference price the run started from, exactly as `tools/feasibility.py`
    measured it. Sessions with a zero or missing close are dropped — there is no
    price to compare against — but a halt day that carries yesterday's close is
    kept, because a price that could not move is still the price that stood.
    """
    usable = [s for s in sessions if s.close > 0]
    out = []
    for i in range(size, len(usable)):
        window = usable[i - size:i + 1]          # size + 1 closes = size sessions
        dates = tuple(s.date for s in window[1:])
        out.append(Window(
            dates=dates,
            gain=window[-1].close / window[0].close - 1,
            holidays=tuple(holidays_between(window[0].date, window[-1].date)),
        ))
    return out


# --- the result -------------------------------------------------------------
@dataclass(frozen=True)
class Momentum:
    """One symbol's latest five-session run, placed in its own distribution.

    `percentile` is `None`, not `0.0`, when there are too few windows to rank
    against: zero would be a measurement ("the weakest run on record") where the
    truth is that nothing was ranked.
    """

    symbol: str
    start: str = ""
    end: str = ""
    n_sessions: int = 0
    explicit_window: bool = False
    window: int = WINDOW
    latest_start: str = ""
    latest_end: str = ""
    latest_gain: float = None
    latest_crosses_holiday: bool = False
    percentile: float = None
    n_windows: int = 0
    median_gain: float = None
    max_gain: float = None
    min_gain: float = None
    all_zero: bool = False
    suspensions_in_window: tuple = ()
    threshold: float = 0.0
    thresholds_version: int = None
    fired: bool = False

    @property
    def suspended(self):
        """An all-zero-volume series is a halted stock, never a quiet one."""
        return self.all_zero

    @property
    def status(self):
        """`suspended` · `tanpa_distribusi` · `biasa` · `teratas`. Descriptive only."""
        if self.all_zero:
            return "suspended"
        if self.percentile is None:
            return "tanpa_distribusi"
        return "teratas" if self.fired else "biasa"

    def __str__(self):
        return describe(self)


def score(symbol, cache=None, thresholds_path=None, start=None, end=None,
          window=WINDOW):
    """Measure the momentum axis for one symbol. Reads the recording only.

    `thresholds_path` is injectable so a test can prove the bar comes from the file
    rather than from this module — an axis with the number baked in passes every
    test that only reads the shipped document.
    """
    want = universe.normalize(symbol)
    data = series(want, cache=cache, start=start, end=end)

    rolling = windows(data.sessions, size=window)
    gains = [w.gain for w in rolling]
    all_zero = data.all_zero

    latest = rolling[-1] if rolling else None
    ranked = len(gains) >= MIN_WINDOWS
    pct = percentile_of(gains, latest.gain) if (latest and ranked) else None

    bar = axes.threshold(AXIS, thresholds_path)
    # A halted stock's closes are carried forward, so its recent windows read as a
    # flat 0% run against a distribution built from the days it was still trading.
    # That is an artefact of the halt, not a measurement, so it never fires.
    fired = bool(pct is not None and not all_zero and pct >= bar)

    return Momentum(
        symbol=want,
        start=data.start,
        end=data.end,
        n_sessions=len(data),
        explicit_window=data.explicit_window,
        window=window,
        latest_start=latest.start if latest else "",
        latest_end=latest.end if latest else "",
        latest_gain=latest.gain if latest else None,
        latest_crosses_holiday=bool(latest and latest.crosses_holiday),
        percentile=pct,
        n_windows=len(gains),
        median_gain=statistics.median(gains) if gains else None,
        max_gain=max(gains) if gains else None,
        min_gain=min(gains) if gains else None,
        all_zero=all_zero,
        suspensions_in_window=(suspensions_in_window(want, data.start, data.end,
                                                     cache=cache)
                               if all_zero else ()),
        threshold=bar,
        thresholds_version=axes.version(thresholds_path),
        fired=fired,
    )


# --- description ------------------------------------------------------------
def _id(value):
    """Format a number the Indonesian way: comma as the decimal separator."""
    return str(value).replace(".", ",")


def _pct(value):
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return sign + _id("%.1f" % (value * 100)) + "%"


def _window_note(result):
    if result.explicit_window:
        return f"{result.n_sessions} sesi, jendela diminta eksplisit"
    return (f"{result.n_sessions} sesi — jendela bawaan /v2/daily/ "
            f"({DEFAULT_WINDOW_SESSIONS} hari), bukan {FULL_WINDOW_SESSIONS}")


def describe(result):
    """A descriptive account of one run. No verdict, no buy/sell, no colour."""
    lines = [f"Momentum {result.symbol} — {result.start} .. {result.end} "
             f"(0 kredit, dari rekaman)",
             f"  jendela          : {_window_note(result)}"]

    if result.all_zero:
        lines.append(f"  deret nol seluruhnya: {result.n_sessions} sesi tanpa satu pun "
                     f"transaksi tercatat; harga penutupan hanya dibawa turun dari "
                     f"sesi terakhir sebelum berhenti.")
        for event in result.suspensions_in_window:
            lines.append(f"  suspensi di dalam jendela: {event.date} — "
                         f"{event.reason_class}")
        if result.suspensions_in_window:
            lines.append("  Deret ini menyertai suspensi: sahamnya dihentikan, bukan "
                         "kehilangan momentum. Tidak ada persentil yang bisa dibaca.")
        else:
            lines.append("  Tidak ada suspensi tercatat di jendela ini, jadi sebab "
                         "deret nol belum diketahui. Tidak ada yang disimpulkan.")
        lines.append(f"  status           : {result.status} · sumbu tidak menyala")
        return "\n".join(lines)

    if result.percentile is None:
        lines += [
            f"  jendela {result.window} sesi : {result.n_windows} buah — "
            f"butuh {MIN_WINDOWS} untuk membentuk distribusi",
            f"  kenaikan terakhir : {_pct(result.latest_gain)}",
            f"  status           : {result.status} · sumbu tidak menyala",
            "  Angka ini deskriptif: apa yang ada di deret harian, bukan penilaian.",
        ]
        return "\n".join(lines)

    lines += [
        f"  jendela terakhir : {result.latest_start} .. {result.latest_end} "
        f"({result.window} sesi bursa)"
        + (" — melewati hari libur bursa, komposisi harinya tidak seimbang"
           if result.latest_crosses_holiday else ""),
        f"  kenaikan 5 sesi  : {_pct(result.latest_gain)}",
        f"  persentil        : {_id('%.0f' % result.percentile)} dari "
        f"{result.n_windows} jendela {result.window} sesi pada saham ini sendiri",
        f"  distribusi saham : median {_pct(result.median_gain)} · "
        f"terendah {_pct(result.min_gain)} · tertinggi {_pct(result.max_gain)}",
        f"  ambang berlaku   : persentil {_id('%.0f' % result.threshold)} "
        f"(ambang v{result.thresholds_version})",
        f"  status           : {result.status} · sumbu "
        f"{'menyala' if result.fired else 'tidak menyala'}",
        "  Persentil dibaca terhadap saham itu sendiri, bukan terhadap pasar: "
        "saham di lapis ini rutin bergerak belasan sampai puluhan persen dalam lima "
        "sesi, jadi persentase mentahnya sendiri tidak berarti apa-apa.",
        "  Angka ini deskriptif: posisi pergerakan terhadap kebiasaan saham itu "
        "sendiri, bukan penilaian atas emiten maupun anjuran tindakan.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    for arg in (sys.argv[1:] or ["LIFE"]):
        print(score(arg))
        print()
