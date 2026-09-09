"""Sumbu volume — the last session measured against the stock's own quiet days.

An absolute volume threshold is meaningless in this universe. These are the 200
smallest listed companies; one of them trades 200 lots a day and another trades
200.000, and both are normal for themselves. So the axis reports a **ratio against
the stock's own history**, never a level.

Three decisions carry the module, and each of them is a mistake this file exists
to avoid.

**The baseline is a median, never a mean.** One auto-rejection-up day inside the
window drags a mean far enough that the *next* spike looks ordinary. LIFE is the
worked example: the mean of its earlier traded sessions is 50.433 and the median is
6.000, so the ratio the reader needs is `147.000 / 6.000 = 24,5x` — not `2,9x`.

**A zero-volume session is not a session.** A halted IDX stock keeps returning
well-formed rows with `volume: 0` and yesterday's close
(`research/docs/api/10-domain-pitfalls.md` §2). Such a day is neither the
numerator nor part of the baseline: it says nothing about how much interest the
stock attracts, only that the exchange stopped the tape. Include it and a halt
quietly drags the baseline down, which inflates the next ratio — the axis then
fires *because* the stock was suspended.

**A series that is nothing but zeros is `suspended`, not `quiet`.** Those are
opposite readings of the same numbers: quiet means nobody wanted the stock,
suspended means nobody was allowed to trade it, and only the first is a fact about
demand. `all_zero` therefore sets `status == "suspended"` and the axis never fires.

And the window itself is a trap. **`/v2/daily/` returns 21 days by default, not
90** — proven live on 9 September 2026 (`riset/temuan-kelayakan.md`, correction 1).
Nothing in the response says so. A baseline written for 90 sessions silently gets
21, so `daily_params()` builds explicit `start`/`end` for every live call and
`Series.explicit_window` records which form actually answered.

Zero credits: reads only `research/harness/recorded/`. `SectorsClient` is never
imported and no socket is opened.
"""
import math
import statistics
from dataclasses import dataclass
from datetime import date, timedelta

from app import axes, config, labels, universe
from app.cache import Cache

AXIS = "volume_anomaly"

DAILY_PATH = "/v2/daily/{symbol}/"

# What the bare call actually returns, and what a baseline actually wants. The gap
# between these two numbers is correction 1 in `riset/temuan-kelayakan.md`.
DEFAULT_WINDOW_SESSIONS = 21
FULL_WINDOW_SESSIONS = 90

# Below this many traded sessions behind the last one there is no distribution to
# compare against, so the ratio is `None` rather than a number computed from three
# observations.
MIN_BASELINE_SESSIONS = 5

# Day-of-week de-seasonalisation is only attempted when every weekday present
# carries at least this many traded sessions. Eight needs roughly forty sessions —
# well past the 21 the bare call returns, which is the point: estimating five
# weekday factors from four observations each would fit noise and then subtract it.
MIN_OBS_PER_WEEKDAY = 8

# Purely descriptive vocabulary for `status`. A ratio under this is reported as
# `quiet` — the last session drew less interest than a normal one. It is not a bar
# anything fires against; the bar lives in `state/thresholds.json`.
QUIET_RATIO = 0.5


class NoDailyDataError(LookupError):
    """No settled `/v2/daily/` payload for this symbol in the recording.

    Raised instead of fetching. The call bills a credit, and a 404 on a guessed
    ticker bills one too, so a missing series is a decision for `capture.py` to
    make deliberately — never a side effect of scoring.
    """


# --- the trading calendar ---------------------------------------------------
def trading_days_back(end, count):
    """The `count` IDX trading days ending on or before `end`, oldest first.

    Holidays are skipped rather than counted, so a request for 90 sessions asks for
    90 sessions and not 90 calendar days containing however many happen to be open.
    `config.is_trading_day` owns the calendar; this walks it.
    """
    out, day, guard = [], end, 0
    while len(out) < count and guard < count * 4 + 30:
        if config.is_trading_day(day):
            out.append(day)
        day -= timedelta(days=1)
        guard += 1
    out.reverse()
    return out


def daily_params(end=None, sessions=FULL_WINDOW_SESSIONS):
    """Explicit `start`/`end` for a live `/v2/daily/` call. Never omit these.

    `SectorsClient` refuses the call without them, and this is the function that
    supplies them: the bare form answers with 21 sessions and says nothing about
    having done so, which is a correctness bug that never looks like one.
    """
    end = end or date.today()
    days = trading_days_back(end, max(int(sessions), 1))
    return {"start": days[0].isoformat(), "end": days[-1].isoformat()}


def holidays_between(first, last):
    """Weekdays inside `(first, last)` on which IDX did not trade.

    Used to mark a window as crossing a holiday. Only weekdays count: a window
    spanning a weekend is every window, and saying so would be noise.
    """
    out, day = [], first + timedelta(days=1)
    while day < last:
        if day.weekday() < 5 and not config.is_trading_day(day):
            out.append(day)
        day += timedelta(days=1)
    return out


# --- the series -------------------------------------------------------------
@dataclass(frozen=True)
class Session:
    """One trading day as `/v2/daily/` returns it. Immutable — nobody re-prices it."""

    symbol: str
    date: date
    close: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    volume: float = 0.0
    market_cap: float = 0.0

    @property
    def traded(self):
        """False on a halt day: a row exists, but no volume changed hands."""
        return self.volume > 0


@dataclass(frozen=True)
class Series:
    """A symbol's daily rows, in date order, with the window that produced them.

    `explicit_window` is the whole reason this wrapper exists. False means the
    payload came from a call with no `start`/`end`, so it holds 21 sessions
    whatever the caller intended, and every number derived from it is a 21-session
    number. It is carried onto the axis results so a reader is told.
    """

    symbol: str
    sessions: tuple = ()
    explicit_window: bool = False
    params: tuple = ()

    def __len__(self):
        return len(self.sessions)

    @property
    def start(self):
        return self.sessions[0].date.isoformat() if self.sessions else ""

    @property
    def end(self):
        return self.sessions[-1].date.isoformat() if self.sessions else ""

    @property
    def traded_sessions(self):
        """Only the days on which trading actually happened."""
        return tuple(s for s in self.sessions if s.traded)

    @property
    def all_zero(self):
        """Every row present, every volume zero. A halt, not an absence of interest."""
        return bool(self.sessions) and not self.traded_sessions


def _settled_param_forms(source, path):
    """Every param form the recording holds for `path`, most explicit first.

    The corpus captured `/v2/daily/{symbol}/` bare on 6 September 2026, before the
    21-day default was known. A later explicit `start`/`end` capture lands under a
    different slug, and this ordering makes the product prefer it the moment one
    exists without any code change.
    """
    forms = []
    for entry in source.manifest().values():
        if (entry.get("path") or "") != path:
            continue
        params = entry.get("params") or {}
        forms.append(params)
    forms.sort(key=lambda p: (0 if ("start" in p and "end" in p) else 1,
                              sorted(p.items())))
    return forms


def _rows(payload):
    """The daily rows, whichever envelope the payload uses."""
    if isinstance(payload, dict):
        payload = payload.get("results") or payload.get("data") or []
    return [r for r in (payload or []) if isinstance(r, dict)]


def _num(row, key):
    try:
        return float(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


def series(symbol, cache=None, start=None, end=None):
    """The settled daily series for `symbol`, or `NoDailyDataError`.

    With `start` and `end` only that exact window is read — the explicit form the
    live API needs. Without them every settled form on record is tried, explicit
    ones first, and the bare 21-session fallback is flagged rather than trusted.
    """
    want = universe.normalize(symbol)
    source = cache if cache is not None else Cache()
    path = DAILY_PATH.format(symbol=want)

    if start is not None and end is not None:
        forms = [{"start": str(start), "end": str(end)}]
    else:
        forms = _settled_param_forms(source, path) or [{}]

    for params in forms:
        hit = source.get(path, params)
        if hit is None or not hit.found:
            continue
        rows = []
        for row in _rows(hit.payload):
            when = labels.parse_date(row.get("date"))
            if when is None:
                continue          # an undated row cannot be placed in a window
            rows.append(Session(
                symbol=want,
                date=when,
                close=_num(row, "close"),
                open=_num(row, "open"),
                high=_num(row, "high"),
                low=_num(row, "low"),
                volume=_num(row, "volume"),
                market_cap=_num(row, "market_cap"),
            ))
        rows.sort(key=lambda s: s.date)
        return Series(symbol=want, sessions=tuple(rows),
                      explicit_window=bool(params.get("start") and params.get("end")),
                      params=tuple(sorted(params.items())))

    raise NoDailyDataError(
        f"Tidak ada deret harian terekam untuk {want!r}. "
        f"Panggilan /v2/daily/ berbiaya 1 kredit dan tidak dijalankan diam-diam — "
        f"ambil lewat capture.py dengan start dan end eksplisit."
    )


def suspensions_in_window(symbol, start, end, cache=None):
    """Suspension announcements dated inside the series' own window.

    A **data-quality check, not a feature**: it is here to answer "is this all-zero
    series a halted stock?", and it deliberately does not go through
    `labels.history_before`, which cannot see inside the window. Nothing derived
    from it may be fed to a model — it explains a hole in the data, it does not
    describe the days before that hole.
    """
    first, last = labels.parse_date(start), labels.parse_date(end)
    if first is None or last is None:
        return ()
    return tuple(labels.events(symbol=symbol, after=first,
                               before=last + timedelta(days=1), cache=cache))


# --- weekly seasonality -----------------------------------------------------
def weekday_factors(sessions, min_obs=MIN_OBS_PER_WEEKDAY):
    """Multiplicative day-of-week factors for volume, or `{}` when data is thin.

    Volume has a weekly shape — Monday and Friday are not Wednesday — and comparing
    a Friday session against a baseline that is mostly midweek measures the calendar
    as much as the stock. The factor is the median **log** volume of that weekday
    against the median log volume overall, so it multiplies rather than shifts, and
    a single ARA day moves it as little as a median can.

    Returns `{}` unless every weekday present carries `min_obs` traded sessions.
    With the 21 rows the bare call returns that is roughly four per weekday, which
    would fit noise and then subtract it — worse than not correcting at all. Thin
    data leaves the raw numbers alone and says so via `deseasonalised`.
    """
    traded = [s for s in sessions if s.traded]
    if len(traded) < min_obs * 2:
        return {}
    buckets = {}
    for session in traded:
        buckets.setdefault(session.date.weekday(), []).append(math.log(session.volume))
    if len(buckets) < 2 or any(len(v) < min_obs for v in buckets.values()):
        return {}
    overall = statistics.median([math.log(s.volume) for s in traded])
    return {day: math.exp(statistics.median(values) - overall)
            for day, values in buckets.items()}


def adjusted_volume(session, factors):
    """Session volume divided by its weekday factor. Unchanged when there are none."""
    factor = factors.get(session.date.weekday(), 1.0) if factors else 1.0
    return session.volume / factor if factor else session.volume


# --- the result -------------------------------------------------------------
@dataclass(frozen=True)
class VolumeAnomaly:
    """One symbol's volume, measured against itself. Immutable — no re-scoring.

    `ratio` is `None`, not `0.0`, when there is no baseline to divide by: zero
    would be a measurement ("no interest at all") where the truth is that nothing
    was measured.
    """

    symbol: str
    start: str = ""
    end: str = ""
    n_sessions: int = 0
    n_traded: int = 0
    n_zero: int = 0
    explicit_window: bool = False
    last_date: str = ""
    last_volume: float = 0.0
    sessions_since_last_trade: int = 0
    baseline_median: float = None
    n_baseline: int = 0
    ratio: float = None
    deseasonalised: bool = False
    weekday_factor: float = 1.0
    all_zero: bool = False
    suspensions_in_window: tuple = ()
    threshold: float = 0.0
    thresholds_version: int = None
    fired: bool = False

    @property
    def suspended(self):
        """An all-zero series is a halted stock, never a quiet one."""
        return self.all_zero

    @property
    def status(self):
        """`suspended` · `tanpa_baseline` · `quiet` · `aktif`. Descriptive only."""
        if self.all_zero:
            return "suspended"
        if self.ratio is None:
            return "tanpa_baseline"
        if self.ratio < QUIET_RATIO:
            return "quiet"
        return "aktif"

    def __str__(self):
        return describe(self)


def score(symbol, cache=None, thresholds_path=None, start=None, end=None):
    """Measure the volume axis for one symbol. Reads the recording only.

    `thresholds_path` is injectable so a test can prove the bar comes from the file
    rather than from this module — an axis with the number baked in passes every
    test that only reads the shipped document.
    """
    want = universe.normalize(symbol)
    data = series(want, cache=cache, start=start, end=end)

    traded = data.traded_sessions
    all_zero = data.all_zero
    factors = weekday_factors(data.sessions)

    ratio = baseline = None
    n_baseline = 0
    last_date = last_volume = 0
    since_last_trade = 0
    weekday_factor = 1.0

    if traded:
        last = traded[-1]
        last_date, last_volume = last.date.isoformat(), last.volume
        weekday_factor = factors.get(last.date.weekday(), 1.0) if factors else 1.0
        # How stale the reading is. Trailing zeros mean the stock is halted *now*,
        # so the ratio describes the last day it was allowed to trade, not today.
        since_last_trade = sum(1 for s in data.sessions if s.date > last.date)

        earlier = [adjusted_volume(s, factors) for s in traded[:-1]]
        n_baseline = len(earlier)
        if n_baseline >= MIN_BASELINE_SESSIONS:
            # Median, not mean: one ARA session in the window would otherwise raise
            # the baseline enough to hide the next one.
            baseline = statistics.median(earlier)
            if baseline > 0:
                ratio = adjusted_volume(last, factors) / baseline

    bar = axes.threshold(AXIS, thresholds_path)
    # An all-zero series never fires. It is not a stock nobody wanted; it is a stock
    # nobody was allowed to trade, and the window's suspension announcements are
    # attached so the reader is told which.
    fired = bool(ratio is not None and not all_zero and ratio >= bar)

    return VolumeAnomaly(
        symbol=want,
        start=data.start,
        end=data.end,
        n_sessions=len(data),
        n_traded=len(traded),
        n_zero=len(data) - len(traded),
        explicit_window=data.explicit_window,
        last_date=last_date,
        last_volume=last_volume,
        sessions_since_last_trade=since_last_trade,
        baseline_median=baseline,
        n_baseline=n_baseline,
        ratio=ratio,
        deseasonalised=bool(factors),
        weekday_factor=weekday_factor,
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


def _lots(value):
    """Volume in the largest unit that stays readable."""
    if value >= 1_000_000_000:
        return _id("%.2f" % (value / 1_000_000_000)) + " miliar"
    if value >= 1_000_000:
        return _id("%.2f" % (value / 1_000_000)) + " juta"
    if value >= 1_000:
        return _id("%.1f" % (value / 1_000)) + " ribu"
    return _id("%.0f" % value)


def _window_note(result):
    if result.explicit_window:
        return f"{result.n_sessions} sesi, jendela diminta eksplisit"
    return (f"{result.n_sessions} sesi — jendela bawaan /v2/daily/ "
            f"({DEFAULT_WINDOW_SESSIONS} hari), bukan {FULL_WINDOW_SESSIONS}")


def describe(result):
    """A descriptive account of one series. No verdict, no buy/sell, no colour."""
    lines = [f"Volume {result.symbol} — {result.start} .. {result.end} "
             f"(0 kredit, dari rekaman)",
             f"  jendela          : {_window_note(result)}"]

    if result.all_zero:
        lines.append(f"  deret nol seluruhnya: {result.n_sessions} sesi tanpa satu pun "
                     f"transaksi tercatat.")
        for event in result.suspensions_in_window:
            lines.append(f"  suspensi di dalam jendela: {event.date} — "
                         f"{event.reason_class}")
        if result.suspensions_in_window:
            lines.append("  Deret ini menyertai suspensi: sahamnya dihentikan, bukan "
                         "sepi peminat. Tidak ada rasio volume yang bisa dibaca.")
        else:
            lines.append("  Tidak ada suspensi tercatat di jendela ini, jadi sebab "
                         "deret nol belum diketahui. Tidak ada yang disimpulkan.")
        lines.append(f"  status           : {result.status} · sumbu tidak menyala")
        return "\n".join(lines)

    if result.ratio is None:
        lines += [
            f"  sesi bertransaksi: {result.n_traded} dari {result.n_sessions}",
            f"  baseline         : belum ada — butuh {MIN_BASELINE_SESSIONS} sesi "
            f"bertransaksi sebelum sesi terakhir, tersedia {result.n_baseline}",
            f"  status           : {result.status} · sumbu tidak menyala",
            "  Angka ini deskriptif: apa yang ada di deret harian, bukan penilaian.",
        ]
        return "\n".join(lines)

    lines += [
        f"  sesi terakhir    : {result.last_date} · volume {_lots(result.last_volume)}"
        + (f" — sudah {result.sessions_since_last_trade} sesi tanpa transaksi sesudahnya"
           if result.sessions_since_last_trade else ""),
        f"  baseline median  : {_lots(result.baseline_median)} dari "
        f"{result.n_baseline} sesi bertransaksi sebelumnya (median, bukan rata-rata)",
        f"  rasio volume     : {_id('%.1f' % result.ratio)}x median sesi sebelumnya",
        f"  sesi nol         : {result.n_zero} dari {result.n_sessions} "
        f"(tidak masuk baseline maupun pembilang)",
        f"  musiman mingguan : "
        + (f"dikoreksi, faktor hari sesi terakhir {_id('%.2f' % result.weekday_factor)}"
           if result.deseasonalised else
           f"tidak dikoreksi — butuh {MIN_OBS_PER_WEEKDAY} sesi per hari-dalam-minggu"),
        f"  ambang berlaku   : {_id('%.2f' % result.threshold)}x "
        f"(ambang v{result.thresholds_version})",
        f"  status           : {result.status} · sumbu "
        f"{'menyala' if result.fired else 'tidak menyala'}",
        "  Angka ini deskriptif: perbandingan volume terhadap kebiasaan saham itu "
        "sendiri, bukan penilaian atas emiten maupun anjuran tindakan.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    for arg in (sys.argv[1:] or ["LIFE"]):
        print(score(arg))
        print()
