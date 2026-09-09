"""The history axis' one rule, and the baseline that is allowed to beat the system.

This axis is the cheapest feature in the product and the easiest place to cheat, so
the tests are built against the plausible wrong implementations rather than merely
against the right one:

  * **reading the suspension file directly.** `labels.events` and
    `labels.load_events` are unbounded in time; either would hand back the event the
    axis is used to predict. `test_history_touches_suspensions_only_through_labels`
    parses `history.py` with `ast` and asserts the only `labels` function it calls is
    `history_before` — an implementation that adds a second door fails even if every
    other test still passes.
  * **a feature that moves when the future arrives.** The real check for leakage is
    not "is the number right" but "is it stable": recompute with events after the
    cutoff appended and the answer must be byte-identical.
  * **scoring the baseline on a friendlier field.** A baseline evaluated only over
    the names it fired on, or with a looser cutoff, is a rigged comparison in the
    system's favour. `run()` must return one prediction per universe member, over
    the same universe the main system screens.
  * **treating 78% as the recidivism a forecaster can see.** It is a hindsight
    number. `test_hindsight_recidivism_is_larger_than_the_leak_safe_one` pins the
    gap — 353/452 against 225/452 — so nobody later quotes the flattering one.

Zero credits: every test reads `research/harness/recorded/` or a temp directory.
Nothing here opens a socket.
"""
import ast
import inspect
import json
from datetime import date

import pytest

from app import cache as cache_mod
from app import labels as labels_mod
from app import universe as universe_mod
from app.axes import history
from app.axes.history import History, as_date, prior_events, score
from app.baselines import previously_suspended as baseline
from app.cache import Cache


def build_cache(tmp_path, suspensions=(), screener=()):
    """A recorded corpus holding the suspensions call, and optionally the screener.

    Written the way `capture.py` writes it — a payload file per slug plus a manifest
    row — so the test exercises the same lookup path the product uses.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest = {}

    def add(path, params, payload):
        key = cache_mod.slug(path, params)
        (tmp_path / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
        manifest[key] = {"path": path, "params": params, "status": 200,
                         "est_cost": 1, "fetched_at": 0, "cost_headers": {}}

    add(labels_mod.SUSPENSIONS_PATH, labels_mod.SUSPENSIONS_PARAMS,
        {"results": list(suspensions)})
    if screener:
        add(universe_mod.SCREENER_PATH, universe_mod.SCREENER_PARAMS,
            {"results": list(screener)})
    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def event(symbol, day, reason="dalam rangka cooling down"):
    return {"symbol": f"{symbol}.JK", "suspension_date": day, "reason": reason}


def company(symbol, cap):
    return {"symbol": f"{symbol}.JK", "company_name": f"PT {symbol}",
            "query_values": {"market_cap": cap}}


LATE_REPORT = "belum menyampaikan laporan keuangan"


# --- the one door -----------------------------------------------------------

def labels_calls():
    """Every `labels.<name>(...)` call made in `history.py`, by name."""
    tree = ast.parse(inspect.getsource(history))
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) \
                and func.value.id == "labels":
            found.add(func.attr)
    return found


def test_history_touches_suspensions_only_through_labels():
    assert labels_calls() == {"history_before"}, (
        "history.py hanya boleh membaca riwayat lewat labels.history_before; "
        f"ditemukan juga: {sorted(labels_calls() - {'history_before'})}")


def test_history_never_opens_the_recording_itself():
    tree = ast.parse(inspect.getsource(history))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(f"{node.module}.{a.name}" for a in node.names)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "open", "history.py tidak boleh membuka berkas"
    forbidden = {"app.cache", "app.cache.Cache", "json", "app.config",
                 "app.config.RECORDED_DIR"}
    assert not (imported & forbidden), (
        f"history.py mengimpor jalur data langsung: {sorted(imported & forbidden)}")


def test_removing_the_accessor_takes_the_whole_axis_with_it(tmp_path, monkeypatch):
    """No fallback path: break `history_before` and nothing else answers."""
    c = build_cache(tmp_path, [event("AAAA", "2026-01-05")])

    def refuse(*args, **kwargs):
        raise AssertionError("pintu ditutup")

    monkeypatch.setattr(labels_mod, "history_before", refuse)
    with pytest.raises(AssertionError):
        score("AAAA", date(2026, 6, 1), cache=c)


# --- leakage ----------------------------------------------------------------

def test_features_do_not_move_when_events_after_the_cutoff_are_added(tmp_path):
    past = [event("AAAA", "2025-02-03"),
            event("AAAA", "2025-11-20", LATE_REPORT),
            event("AAAA", "2026-04-01")]
    future = [event("AAAA", "2026-06-10"),      # the cutoff day itself
              event("AAAA", "2026-06-11"),
              event("AAAA", "2026-08-30", LATE_REPORT)]

    before = score("AAAA", date(2026, 6, 10), cache=build_cache(tmp_path / "a", past))
    after = score("AAAA", date(2026, 6, 10),
                  cache=build_cache(tmp_path / "b", past + future))
    assert before == after


def test_the_cutoff_day_itself_is_the_future(tmp_path):
    c = build_cache(tmp_path, [event("AAAA", "2026-06-10")])
    assert score("AAAA", date(2026, 6, 10), cache=c).n_prior == 0
    assert score("AAAA", date(2026, 6, 11), cache=c).n_prior == 1


def test_a_cutoff_is_required(tmp_path):
    c = build_cache(tmp_path, [event("AAAA", "2026-01-05")])
    with pytest.raises(ValueError):
        score("AAAA", None, cache=c)
    with pytest.raises(ValueError):
        prior_events("AAAA", "bukan tanggal", cache=c)


# --- the features -----------------------------------------------------------

def test_never_suspended_reports_no_distance_rather_than_zero(tmp_path):
    c = build_cache(tmp_path, [event("BBBB", "2026-01-05")])
    got = score("AAAA", date(2026, 6, 1), cache=c)
    assert got.n_prior == 0
    assert got.days_since_last is None, "nol hari berarti disuspensi hari ini"
    assert got.status == "tanpa_riwayat"


def test_counts_days_and_classes_across_all_nine_classes(tmp_path):
    c = build_cache(tmp_path, [
        event("AAAA", "2019-03-01", LATE_REPORT),
        event("AAAA", "2025-02-03"),
        event("AAAA", "2026-05-01", LATE_REPORT),
    ])
    got = score("AAAA", date(2026, 6, 10), cache=c)
    assert got.n_prior == 3                     # pre-2025 history still counts
    assert got.n_prior_label == 1               # only one is cooling-down
    assert dict(got.reason_counts) == {"cooling_down": 1, "late_report": 2}
    assert got.last_date == "2026-05-01"
    assert got.last_reason_class == "late_report"
    assert got.days_since_last == (date(2026, 6, 10) - date(2026, 5, 1)).days
    assert got.status == "pernah_cooling_down"

    # A record made only of other classes is history too, and says so differently.
    other = build_cache(tmp_path / "other", [event("AAAA", "2019-03-01", LATE_REPORT)])
    assert score("AAAA", date(2026, 6, 10), cache=other).status == "pernah_disuspensi"


def test_string_and_date_cutoffs_agree(tmp_path):
    c = build_cache(tmp_path, [event("AAAA", "2026-01-05")])
    assert score("AAAA", "2026-06-10", cache=c) == score("AAAA", date(2026, 6, 10),
                                                         cache=c)
    assert as_date("2026-06-10") == date(2026, 6, 10)
    assert as_date("kemarin") is None


def test_describe_states_the_record_without_a_verdict(tmp_path):
    c = build_cache(tmp_path, [event("AAAA", "2026-01-05")])
    text = str(score("AAAA", date(2026, 6, 10), cache=c))
    assert "2026-01-05" in text
    for word in ("beli", "jual", "hindari", "rekomendasi", "sinyal"):
        assert word not in text.lower()


# --- the baseline -----------------------------------------------------------

def universe_cache(tmp_path):
    """Four listed companies, two of them with a suspension on record."""
    return build_cache(
        tmp_path,
        suspensions=[event("AAAA", "2025-02-03"),
                     event("BBBB", "2019-03-01", LATE_REPORT),
                     event("ZZZZ", "2026-01-01")],     # not in the universe
        screener=[company("AAAA", 100), company("BBBB", 200),
                  company("CCCC", 300), company("DDDD", 400)])


def test_baseline_predicts_for_the_same_universe_as_the_main_system(tmp_path):
    c = universe_cache(tmp_path)
    got = baseline.run(date(2026, 6, 10), cache=c)
    assert [p.symbol for p in got] == universe_mod.watchlist(cache=c)
    assert len(got) == 4, "prediksi wajib mencakup emiten yang tidak diperingatkan juga"
    assert {p.symbol for p in baseline.warned(got)} == {"AAAA", "BBBB"}
    assert {p.symbol for p in got if not p.warned} == {"CCCC", "DDDD"}


def test_baseline_warns_on_any_reason_class_not_only_the_label_class(tmp_path):
    c = universe_cache(tmp_path)
    got = {p.symbol: p for p in baseline.run(date(2026, 6, 10), cache=c)}
    assert got["BBBB"].warned and got["BBBB"].n_prior_label == 0


def test_baseline_uses_exactly_the_same_time_separation(tmp_path):
    """Its cutoff is the axis' cutoff: post-cutoff events change nothing."""
    early = build_cache(tmp_path / "a", [event("AAAA", "2025-02-03")],
                        [company("AAAA", 100), company("CCCC", 300)])
    late = build_cache(tmp_path / "b",
                       [event("AAAA", "2025-02-03"), event("CCCC", "2026-06-10"),
                        event("CCCC", "2026-07-01")],
                       [company("AAAA", 100), company("CCCC", 300)])
    assert baseline.run(date(2026, 6, 10), cache=early) == baseline.run(
        date(2026, 6, 10), cache=late)


def test_baseline_cutoff_is_required(tmp_path):
    c = universe_cache(tmp_path)
    with pytest.raises(ValueError):
        baseline.run(None, cache=c)


def test_baseline_describes_itself_without_claiming_to_be_a_straw_man(tmp_path):
    text = baseline.describe(baseline.run(date(2026, 6, 10), cache=universe_cache(tmp_path)))
    assert "4 emiten" in text and "2 (50%)" in text
    assert "dikalahkan" in text


# --- against the live recording ---------------------------------------------

def test_hindsight_recidivism_is_larger_than_the_leak_safe_one():
    """78% is measured after the fact; 50% is what a forecaster could see.

    Both come from the same 452 label events. The first counts every event of a
    symbol that repeats — including its first, when there was nothing to memorise.
    The second asks `history_before` on the day, which is the only one a feature may
    use. Asserting the gap keeps the flattering number from being quoted as if it
    were the useful one.
    """
    events = labels_mod.label_events()
    per_symbol = {}
    for e in events:
        per_symbol[e.symbol] = per_symbol.get(e.symbol, 0) + 1
    hindsight = sum(n for n in per_symbol.values() if n > 1)

    leak_safe = sum(1 for e in events if score(e.symbol, e.date).n_prior > 0)

    assert (len(events), hindsight) == (452, 353)
    assert leak_safe == 225
    assert leak_safe < hindsight


def test_baseline_fires_on_half_the_working_universe():
    """98 of 200 — the same 98 `universe.control_group` excludes."""
    got = baseline.run(date(2026, 9, 1))
    assert len(got) == 200
    fired = {p.symbol for p in baseline.warned(got)}
    assert len(fired) == 98
    assert not fired & set(universe_mod.control_group())
