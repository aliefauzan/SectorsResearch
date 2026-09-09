"""The two daily-series axes, and the four ways they would go wrong quietly.

Each of these has a test built to fail against the plausible wrong implementation
rather than merely to pass against the right one:

  * **a mean baseline.** LIFE's earlier traded sessions average 50.433 and their
    median is 6.000. The mean makes a 24,5x session read as 2,9x — still a number,
    still plausible, and wrong. `test_life_volume_ratio_matches_the_task_figure` and
    `test_a_mean_baseline_would_hide_the_spike` pin the median.
  * **counting a halt as a quiet day.** A suspended IDX stock returns well-formed
    rows with `volume: 0`. Averaged into the baseline they drag it down and inflate
    the next ratio, so the axis fires *because* the stock was halted.
  * **calling an all-zero series quiet.** Quiet means nobody wanted it; suspended
    means nobody could trade it. `test_an_all_zero_series_is_suspended_not_quiet`
    is the task's own criterion.
  * **an absolute percentage bar.** These stocks move 13–29% in five sessions on an
    ordinary week (§Q3), so the axis ranks a window against the stock's own
    distribution. `test_the_strongest_window_is_percentile_100` and
    `test_the_median_five_session_gain_matches_the_feasibility_note` hold that.

Windows are also checked against the trading calendar: five sessions across the
17 August 2026 holiday must still be five real dates and never a synthesised empty
day at a closed-market price.

Zero credits: everything reads `research/harness/recorded/` or a temp directory.
`test_a_missing_series_raises_instead_of_fetching` is the one that proves no socket
is opened.
"""
import json
import statistics
from datetime import date

import pytest

from app import cache as cache_mod
from app.axes import momentum, volume_anomaly
from app.axes.momentum import MIN_WINDOWS, WINDOW, percentile_of, windows
from app.axes.volume_anomaly import (
    MIN_BASELINE_SESSIONS,
    MIN_OBS_PER_WEEKDAY,
    NoDailyDataError,
    Session,
    daily_params,
    series,
    trading_days_back,
    weekday_factors,
)
from app.cache import Cache


# --- fixtures ---------------------------------------------------------------
def rows(symbol, start_dates, closes, volumes):
    """`/v2/daily/` rows, one per date, in the shape the live API returns."""
    return [{"symbol": f"{symbol}.JK", "date": d, "close": c, "open": c,
             "high": c, "low": c, "volume": v, "market_cap": c * 1_000_000}
            for d, c, v in zip(start_dates, closes, volumes)]


def build_cache(tmp_path, dailies=(), suspensions=()):
    """A recorded corpus holding daily series and the suspension source.

    Written the way `capture.py` writes it — one payload file per slug plus a
    manifest row — so the test exercises the same lookup the product uses live.
    """
    from app import labels as labels_mod

    manifest = {}

    def add(path, params, payload):
        key = cache_mod.slug(path, params)
        (tmp_path / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
        manifest[key] = {"path": path, "params": params, "status": 200,
                         "est_cost": 1, "fetched_at": 0, "cost_headers": {}}

    for symbol, params, payload in dailies:
        add(volume_anomaly.DAILY_PATH.format(symbol=symbol), params, payload)
    if suspensions:
        add(labels_mod.SUSPENSIONS_PATH, labels_mod.SUSPENSIONS_PARAMS,
            {"results": list(suspensions)})

    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def thresholds_file(tmp_path, volume=5.0, momentum_bar=90.0, bounds=None, version=9):
    tmp_path.mkdir(parents=True, exist_ok=True)
    doc = {"version": version, "updated_on": "2026-09-09",
           "current": {volume_anomaly.AXIS: volume, momentum.AXIS: momentum_bar},
           "cohort_factors": {}, "history": []}
    if bounds is not None:
        doc["bounds"] = bounds
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


def sessions_from(dates, closes, volumes, symbol="AAAA"):
    """Sessions built directly, for the helpers that do not need a cache."""
    return [Session(symbol=symbol, date=date(*(int(p) for p in d.split("-"))),
                    close=c, volume=v)
            for d, c, v in zip(dates, closes, volumes)]


# --- the headline number ----------------------------------------------------
def test_life_volume_ratio_matches_the_task_figure():
    """The task's own criterion: LIFE reads ~24,5x. 147.000 over a median of 6.000."""
    result = volume_anomaly.score("LIFE")
    assert round(result.ratio, 1) == 24.5
    assert result.baseline_median == 6000
    assert result.last_volume == 147000
    assert result.fired is True


def test_a_mean_baseline_would_hide_the_spike():
    """A mean is not a slightly different answer — it is a different reading."""
    data = series("LIFE")
    earlier = [s.volume for s in data.traded_sessions[:-1]]
    last = data.traded_sessions[-1].volume
    assert round(last / statistics.mean(earlier), 1) == 2.9      # what a mean says
    assert round(last / statistics.median(earlier), 1) == 24.5   # what the axis says


def test_the_median_five_session_gain_matches_the_feasibility_note():
    """§Q3's table: LIFE 23,8%, TRUK 21,4%, SAFE 25,0%, TMPO -3,8%."""
    expected = {"LIFE": 23.8, "TRUK": 21.4, "SAFE": 25.0, "TMPO": -3.8}
    for symbol, median in expected.items():
        assert round(momentum.score(symbol).median_gain * 100, 1) == median


# --- zero volume ------------------------------------------------------------
def test_an_all_zero_series_is_suspended_not_quiet(tmp_path):
    """The task's criterion: a zero series is a halt, not an anomaly and not quiet."""
    dates = ["2026-08-10", "2026-08-11", "2026-08-12", "2026-08-13", "2026-08-14",
             "2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21", "2026-08-24"]
    closes = [1000] * 10
    c = build_cache(tmp_path,
                    dailies=[("AAAA", {}, rows("AAAA", dates, closes, [0] * 10))],
                    suspensions=[{"symbol": "AAAA.JK", "suspension_date": "2026-08-11",
                                  "reason": "peningkatan harga kumulatif yang signifikan"}])
    path = thresholds_file(tmp_path)

    volume = volume_anomaly.score("AAAA", cache=c, thresholds_path=path)
    assert volume.all_zero is True
    assert volume.suspended is True
    assert volume.status == "suspended"
    assert volume.status != "quiet"
    assert volume.ratio is None
    assert volume.fired is False
    assert [e.reason_class for e in volume.suspensions_in_window] == ["cooling_down"]

    run = momentum.score("AAAA", cache=c, thresholds_path=path)
    assert run.suspended is True
    assert run.status == "suspended"
    assert run.fired is False


def test_a_zero_session_is_neither_the_numerator_nor_the_baseline(tmp_path):
    """A halt day would drag the median down and inflate the next ratio."""
    dates = ["2026-08-10", "2026-08-11", "2026-08-12", "2026-08-13", "2026-08-14",
             "2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21", "2026-08-24",
             "2026-08-26"]
    volumes = [100, 100, 100, 100, 100, 0, 0, 0, 0, 0, 900]
    c = build_cache(tmp_path,
                    dailies=[("AAAA", {}, rows("AAAA", dates, [1000] * 11, volumes))])
    result = volume_anomaly.score("AAAA", cache=c,
                                  thresholds_path=thresholds_file(tmp_path))
    # Six sessions traded; the baseline is the five before the last, all of them 100.
    assert result.n_traded == 6
    assert result.n_baseline == 5
    assert result.n_zero == 5
    assert result.baseline_median == 100
    assert result.ratio == 9.0
    # Counting the five halt days would halve the median and double the ratio: the
    # axis would then read as an anomaly precisely because the stock was halted.
    assert statistics.median(volumes[:-1]) == 50
    assert 900 / statistics.median(volumes[:-1]) == 18.0


def test_a_quiet_stock_is_reported_as_quiet_not_as_a_halt(tmp_path):
    """The opposite reading: real trading, just less of it than usual."""
    dates = ["2026-08-10", "2026-08-11", "2026-08-12", "2026-08-13", "2026-08-14",
             "2026-08-18", "2026-08-19"]
    c = build_cache(tmp_path, dailies=[
        ("AAAA", {}, rows("AAAA", dates, [1000] * 7, [1000] * 6 + [100]))])
    result = volume_anomaly.score("AAAA", cache=c,
                                  thresholds_path=thresholds_file(tmp_path))
    assert result.all_zero is False
    assert result.status == "quiet"
    assert result.ratio == 0.1
    assert result.fired is False


def test_too_few_traded_sessions_gives_no_ratio_rather_than_a_number(tmp_path):
    """`None`, not `0.0`: nothing was measured, which is not the same as zero."""
    dates = ["2026-08-10", "2026-08-11", "2026-08-12", "2026-08-13"]
    c = build_cache(tmp_path,
                    dailies=[("AAAA", {}, rows("AAAA", dates, [1000] * 4, [10] * 4))])
    result = volume_anomaly.score("AAAA", cache=c,
                                  thresholds_path=thresholds_file(tmp_path))
    assert result.n_baseline < MIN_BASELINE_SESSIONS
    assert result.ratio is None
    assert result.status == "tanpa_baseline"
    assert result.fired is False


# --- percentiles ------------------------------------------------------------
def test_the_strongest_window_is_percentile_100():
    """The task's criterion, on the live recording rather than a fixture."""
    for symbol in ("LIFE", "TRUK", "SAFE", "TMPO"):
        gains = [w.gain for w in windows(series(symbol).sessions)]
        assert percentile_of(gains, max(gains)) == 100.0
        # The weakest window cannot reach 100 unless every window ties with it.
        assert percentile_of(gains, min(gains)) < 100.0


def test_the_percentile_is_monotone_in_the_gain():
    gains = [-0.1, 0.0, 0.2, 0.5, 1.0]
    ranks = [percentile_of(gains, g) for g in gains]
    assert ranks == sorted(ranks)
    assert ranks[-1] == 100.0


def test_a_symbol_whose_latest_window_is_its_strongest_reads_100(tmp_path):
    dates = ["2026-08-%02d" % d for d in (10, 11, 12, 13, 14, 18, 19, 20, 21, 24)] \
        + ["2026-08-26", "2026-08-27", "2026-08-28", "2026-08-31", "2026-09-01"]
    closes = [100, 101, 100, 102, 101, 100, 102, 101, 103, 102, 140, 190, 260, 350, 480]
    c = build_cache(tmp_path,
                    dailies=[("AAAA", {}, rows("AAAA", dates, closes, [500] * 15))])
    result = momentum.score("AAAA", cache=c,
                            thresholds_path=thresholds_file(tmp_path))
    assert result.n_windows >= MIN_WINDOWS
    assert result.percentile == 100.0
    assert result.fired is True
    assert result.status == "teratas"


def test_a_thin_series_gives_no_percentile_rather_than_a_rank_out_of_three(tmp_path):
    dates = ["2026-08-%02d" % d for d in (10, 11, 12, 13, 14, 18, 19)]
    c = build_cache(tmp_path, dailies=[
        ("AAAA", {}, rows("AAAA", dates, [100, 110, 120, 130, 140, 150, 160],
                          [500] * 7))])
    result = momentum.score("AAAA", cache=c,
                            thresholds_path=thresholds_file(tmp_path))
    assert result.n_windows < MIN_WINDOWS
    assert result.percentile is None
    assert result.status == "tanpa_distribusi"
    assert result.fired is False


def test_an_absolute_percentage_is_not_the_axis():
    """A 10,2% run in LIFE sits at percentile 44 — below its own median week."""
    result = momentum.score("LIFE")
    assert round(result.latest_gain * 100, 1) == 10.2
    assert result.percentile < 50
    assert result.fired is False


# --- the trading calendar ---------------------------------------------------
def test_a_window_crossing_a_holiday_has_no_empty_days():
    """17 August 2026 is a Monday and IDX is closed. Five sessions stay five dates."""
    dates = ["2026-08-10", "2026-08-11", "2026-08-12", "2026-08-13", "2026-08-14",
             "2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21", "2026-08-24"]
    built = sessions_from(dates, [100 + i for i in range(10)], [500] * 10)
    crossing = [w for w in windows(built) if w.crosses_holiday]
    assert crossing, "expected at least one window spanning 17 August"
    for window in crossing:
        assert window.sessions == WINDOW
        assert len(set(window.dates)) == WINDOW
        assert all(d.isoformat() in dates for d in window.dates)
        assert date(2026, 8, 17) not in window.dates
        assert [d for d in window.holidays] == [date(2026, 8, 17)]


def test_every_window_holds_exactly_five_real_trading_dates():
    from app import config

    for window in windows(series("LIFE").sessions):
        assert window.sessions == WINDOW
        assert all(config.is_trading_day(d) for d in window.dates)


def test_trading_days_back_skips_holidays_and_weekends():
    days = trading_days_back(date(2026, 8, 20), 5)
    assert [d.isoformat() for d in days] == [
        "2026-08-13", "2026-08-14", "2026-08-18", "2026-08-19", "2026-08-20"]


def test_daily_params_asks_for_an_explicit_window():
    """The bare call returns 21 sessions and never says so. So never make it bare."""
    params = daily_params(end=date(2026, 8, 20), sessions=5)
    assert params == {"start": "2026-08-13", "end": "2026-08-20"}

    from app.sectors_client import check_params
    check_params("/v2/daily/LIFE/", params)                      # accepted
    with pytest.raises(Exception):
        check_params("/v2/daily/LIFE/", {})                      # refused


def test_the_bare_recorded_window_is_flagged_not_trusted():
    data = series("LIFE")
    assert data.explicit_window is False
    assert len(data) == volume_anomaly.DEFAULT_WINDOW_SESSIONS
    assert "bukan 90" in str(volume_anomaly.score("LIFE"))


def test_an_explicit_recording_is_preferred_over_the_bare_one(tmp_path):
    dates = ["2026-08-%02d" % d for d in (10, 11, 12, 13, 14, 18)]
    c = build_cache(tmp_path, dailies=[
        ("AAAA", {}, rows("AAAA", dates[:3], [100] * 3, [10] * 3)),
        ("AAAA", {"start": "2026-08-10", "end": "2026-08-18"},
         rows("AAAA", dates, [100] * 6, [10] * 6)),
    ])
    data = series("AAAA", cache=c)
    assert data.explicit_window is True
    assert len(data) == 6


# --- weekly seasonality -----------------------------------------------------
def test_seasonality_is_not_estimated_from_a_handful_of_sessions():
    """21 sessions is ~4 per weekday. Fitting five factors on that fits noise."""
    assert weekday_factors(series("LIFE").sessions) == {}
    assert volume_anomaly.score("LIFE").deseasonalised is False


def test_seasonality_is_removed_once_there_are_enough_sessions():
    """Mondays at 10x the other days: the factor lifts them back onto the baseline."""
    from app import config

    dates, volumes, day = [], [], date(2026, 3, 2)
    while len(dates) < MIN_OBS_PER_WEEKDAY * 5 + 20:
        if config.is_trading_day(day):
            dates.append(day.isoformat())
            volumes.append(10_000 if day.weekday() == 0 else 1_000)
        day = date.fromordinal(day.toordinal() + 1)

    built = sessions_from(dates, [100] * len(dates), volumes)
    factors = weekday_factors(built)
    assert factors, "expected factors once every weekday has enough sessions"
    assert round(factors[0] / factors[1], 1) == 10.0

    adjusted = [volume_anomaly.adjusted_volume(s, factors) for s in built]
    # After correction a Monday and a Tuesday sit at the same level, so a Monday no
    # longer reads as a tenfold anomaly purely for being a Monday.
    mondays = [a for s, a in zip(built, adjusted) if s.date.weekday() == 0]
    others = [a for s, a in zip(built, adjusted) if s.date.weekday() == 1]
    assert round(statistics.median(mondays) / statistics.median(others), 2) == 1.0


# --- thresholds and credits -------------------------------------------------
def test_the_bar_comes_from_the_file_not_from_the_module(tmp_path):
    high = thresholds_file(tmp_path / "a", volume=1000.0, momentum_bar=999.0)
    low = thresholds_file(tmp_path / "b", volume=1.0, momentum_bar=1.0)
    assert volume_anomaly.score("LIFE", thresholds_path=high).fired is False
    assert volume_anomaly.score("LIFE", thresholds_path=low).fired is True
    assert momentum.score("LIFE", thresholds_path=high).fired is False
    assert momentum.score("LIFE", thresholds_path=low).fired is True


def test_the_answer_records_which_threshold_version_produced_it(tmp_path):
    path = thresholds_file(tmp_path, version=42)
    assert volume_anomaly.score("LIFE", thresholds_path=path).thresholds_version == 42
    assert momentum.score("LIFE", thresholds_path=path).thresholds_version == 42


def test_a_bound_caps_a_threshold_that_walked_too_far(tmp_path):
    path = thresholds_file(tmp_path, volume=999.0,
                           bounds={volume_anomaly.AXIS: {"floor": 2.0, "ceiling": 30.0}})
    assert volume_anomaly.score("LIFE", thresholds_path=path).threshold == 30.0


def test_a_missing_series_raises_instead_of_fetching(tmp_path):
    """A missing series is a capture decision, never a side effect of scoring."""
    c = build_cache(tmp_path, dailies=[])
    with pytest.raises(NoDailyDataError):
        volume_anomaly.score("ZZZZ", cache=c)
    with pytest.raises(NoDailyDataError):
        momentum.score("ZZZZ", cache=c)


def test_neither_axis_imports_the_client():
    """The axes read the recording. Nothing in either module may open a socket."""
    for module in (volume_anomaly, momentum):
        source = open(module.__file__, encoding="utf-8").read()
        assert "sectors_client" not in source
        assert "urllib" not in source


# --- output ------------------------------------------------------------------
def test_the_description_is_descriptive_and_in_indonesian():
    text = str(volume_anomaly.score("LIFE")) + "\n" + str(momentum.score("LIFE"))
    assert "24,5x" in text
    assert "deskriptif" in text
    for verdict in ("beli", "jual", "rekomendasi", "sinyal", "target harga"):
        assert verdict not in text.lower()
