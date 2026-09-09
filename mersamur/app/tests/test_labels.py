"""The label set's three invariants: no leakage, one regime, the right classes.

The counts here are asserted against the live recording on purpose — they are the
numbers in `riset/temuan-kelayakan.md` §Q4, and a silent drift between the note
and the code is exactly what this file exists to catch. The leakage tests build
their own tiny corpus instead, because a boundary rule must hold for any data.
"""
import json
from datetime import date

import pytest

from app import cache as cache_mod
from app.cache import Cache
from app.labels import (
    LABEL_CLASS,
    REASON_CLASSES,
    REGIME_START,
    SUSPENSIONS_PARAMS,
    SUSPENSIONS_PATH,
    Event,
    base_rate,
    classify,
    counts_by_year,
    events,
    history_before,
    label_events,
    load_events,
    reason_counts,
    summary,
)


def build_cache(tmp_path, rows):
    """Write a one-call recorded corpus the way capture.py does."""
    key = cache_mod.slug(SUSPENSIONS_PATH, SUSPENSIONS_PARAMS)
    (tmp_path / f"{key}.json").write_text(
        json.dumps({"results": rows, "pagination": {"total_count": len(rows)}}),
        encoding="utf-8")
    (tmp_path / "_manifest.json").write_text(json.dumps({key: {
        "path": SUSPENSIONS_PATH, "params": SUSPENSIONS_PARAMS, "status": 200,
        "est_cost": 20, "fetched_at": 0, "cost_headers": {}}}), encoding="utf-8")
    return Cache(root=str(tmp_path))


def row(symbol, day, reason="dalam rangka cooling down"):
    return {"symbol": f"{symbol}.JK", "suspension_date": day, "reason": reason}


# --- leakage ---------------------------------------------------------------

def test_history_before_never_returns_events_at_or_after_the_cutoff(tmp_path):
    c = build_cache(tmp_path, [
        row("AAAA", "2026-03-01"),
        row("AAAA", "2026-06-10"),   # the cutoff day itself
        row("AAAA", "2026-06-11"),
        row("AAAA", "2026-09-01"),
    ])
    got = history_before("AAAA", date(2026, 6, 10), cache=c)
    assert [e.date for e in got] == [date(2026, 3, 1)]
    assert all(e.date < date(2026, 6, 10) for e in got)


def test_history_before_is_exclusive_on_every_day_of_the_record(tmp_path):
    days = ["2026-01-05", "2026-02-09", "2026-03-16"]
    c = build_cache(tmp_path, [row("BBBB", d) for d in days])
    for d in days:
        cutoff = date(*(int(v) for v in d.split("-")))
        assert all(e.date < cutoff for e in history_before("BBBB", cutoff, cache=c))


def test_history_before_does_not_leak_across_symbols(tmp_path):
    c = build_cache(tmp_path, [row("AAAA", "2026-01-05"), row("BBBB", "2026-01-06")])
    assert [e.symbol for e in history_before("AAAA", date(2026, 12, 31), cache=c)] == ["AAAA"]


def test_history_before_requires_a_cutoff(tmp_path):
    c = build_cache(tmp_path, [row("AAAA", "2026-01-05")])
    with pytest.raises(ValueError):
        history_before("AAAA", None, cache=c)


def test_events_bounds_are_before_exclusive_after_inclusive(tmp_path):
    c = build_cache(tmp_path, [row("AAAA", d) for d in
                               ("2026-01-05", "2026-02-05", "2026-03-05")])
    got = events("AAAA", after=date(2026, 2, 5), before=date(2026, 3, 5), cache=c)
    assert [e.date for e in got] == [date(2026, 2, 5)]


# --- regime ----------------------------------------------------------------

def test_pre_2025_events_are_not_in_the_label_set(tmp_path):
    c = build_cache(tmp_path, [row("AAAA", "2024-12-31"), row("AAAA", "2025-01-01")])
    assert [e.date for e in label_events(cache=c)] == [date(2025, 1, 1)]


def test_pre_2025_events_are_still_in_the_archive_and_in_history(tmp_path):
    """Dropped as a label, kept as a feature — those are different decisions."""
    c = build_cache(tmp_path, [row("AAAA", "2024-12-31")])
    assert len(load_events(cache=c)) == 1
    assert len(history_before("AAAA", date(2026, 1, 1), cache=c)) == 1
    assert label_events(cache=c) == []


def test_live_record_has_no_cooling_down_before_the_regime_start():
    assert [e for e in events(before=REGIME_START, reason_class=LABEL_CLASS)] == []


# --- reason classes --------------------------------------------------------

def test_cooling_down_matches_without_the_price_preamble():
    """The 17-event bug: 'cooling down' also appears with no 'peningkatan' prefix."""
    assert classify("Dalam rangka cooling down sebagai perlindungan investor") == "cooling_down"
    assert classify("Terjadinya peningkatan harga kumulatif yang signifikan") == "cooling_down"


def test_reason_counts_match_the_feasibility_note():
    """The table in riset/temuan-kelayakan.md §Q4, asserted against the recording."""
    counts = reason_counts()
    assert counts["cooling_down"] == 452
    assert counts["long_suspend"] == 56
    assert counts["rule_I_A"] == 25
    assert counts["late_report"] == 16
    assert counts["price_decline"] == 10
    assert counts["going_concern"] == 7
    assert counts["ppk_over_1y"] == 7
    assert counts["delisting"] == 3
    assert counts["other"] == 9
    assert sum(counts.values()) == 585
    assert set(counts) <= set(REASON_CLASSES)


def test_pre_2025_classes_match_the_note():
    by_year = counts_by_year()
    pre = {}
    for year, counter in by_year.items():
        if year < REGIME_START.year:
            for name, n in counter.items():
                pre[name] = pre.get(name, 0) + n
    assert pre == {"long_suspend": 53}


def test_going_concern_is_never_a_label():
    """A different problem. Using it as a target would answer the wrong question."""
    assert all(e.reason_class == LABEL_CLASS for e in label_events())
    assert any(e.reason_class == "going_concern" for e in load_events())


# --- the headline numbers --------------------------------------------------

def test_label_set_size_and_unique_symbols():
    labels = label_events()
    assert len(labels) == 452
    assert len({e.symbol for e in labels}) == 236
    assert all(e.date >= REGIME_START for e in labels)


def test_base_rate_2026():
    rate = base_rate(2026)
    assert rate["events"] == 120
    assert round(rate["per_stock_10d"] * 100, 2) == 0.77


def test_summary_reports_the_numbers_descriptively():
    text = summary()
    assert "452" in text and "236" in text and "0,77%" in text
    for verdict in ("beli", "jual", "rekomendasi", "sinyal"):
        assert verdict not in text.lower()


# --- shape -----------------------------------------------------------------

def test_symbols_are_stripped_of_the_jk_suffix(tmp_path):
    c = build_cache(tmp_path, [row("AAAA", "2026-01-05")])
    assert load_events(cache=c)[0].symbol == "AAAA"


def test_events_are_sorted_and_immutable(tmp_path):
    c = build_cache(tmp_path, [row("BBBB", "2026-03-05"), row("AAAA", "2026-01-05")])
    got = load_events(cache=c)
    assert [e.date for e in got] == [date(2026, 1, 5), date(2026, 3, 5)]
    with pytest.raises(Exception):
        got[0].date = date(2020, 1, 1)


def test_undated_rows_are_dropped(tmp_path):
    c = build_cache(tmp_path, [row("AAAA", None), row("AAAA", "2026-01-05")])
    assert len(load_events(cache=c)) == 1


def test_missing_recording_yields_an_empty_set_not_a_crash(tmp_path):
    (tmp_path / "_manifest.json").write_text("{}", encoding="utf-8")
    c = Cache(root=str(tmp_path))
    assert load_events(cache=c) == []
    assert label_events(cache=c) == []
    assert base_rate(2026, cache=c) is None
