"""What the PELAJARI step must never do: skip a lesson, or write half of one.

Task 16 names three tests, and each answers the judge's question in a different
place in the file:

  * **one lesson per outcome.** A settled warning that produced no lesson is a
    warning the system never learned from, and a settled warning that produced two
    would double-count in task 17's twenty-outcome guard.
  * **six fields, none empty.** The whole point of the structure is that it can be
    aggregated and shown on screen. `axis_implicated: null` or `subsector: ""`
    would pass `ledger.validate` and be useless to both.
  * **`recent()` respects the window.** Step 3 injects the last thirty days into
    the next screen. A window that leaks older rows quietly turns a loop that
    forgets into one that never does.

The rest cover the two asymmetries the task rests on: the right answers teach too
(step 2), and a subsector comes from a payload that was paid for rather than from
a guess.

Zero credits: every corpus below is a handful of files in `tmp_path`, and no
client is constructed anywhere in this file.
"""
import json

import pytest

from app import cache as cache_mod, ledger
from app.agent import lessons

from datetime import date


# --- fixtures ---------------------------------------------------------------
def warning(wid, symbol, day, axes=None, fired=4):
    """A four-axis warning row, valid against `ledger.WARNING_SCHEMA`."""
    default = {
        "concentration": {"value": 0.61, "threshold": 0.45, "fired": True},
        "volume_anomaly": {"value": 8.2, "threshold": 3.0, "fired": True},
        "momentum": {"value": 0.92, "threshold": 0.90, "fired": True},
        "catalyst": {"value": 0.05, "threshold": 0.20, "fired": True},
    }
    return {
        "id": wid, "symbol": symbol, "date": day,
        "axes": axes or default,
        "axes_fired": fired, "axes_total": 4, "thresholds_version": 3,
        "prediction": ledger.PREDICTION, "credits_spent": 4, "status": "open",
    }


def hit(wid, resolved_on="2026-09-10", suspension_date="2026-09-04", days=7):
    return {
        "warning_id": wid, "resolved_on": resolved_on, "outcome": "true_positive",
        "days_elapsed": days,
        "evidence": {"source": "/v2/suspensions/", "suspension_date": suspension_date,
                     "reason_class": "cooling_down",
                     "pdf_url": "https://www.idx.co.id/x.pdf"},
    }


def miss(wid, resolved_on="2026-09-10", checked_through="2026-09-10", days=10,
         price=None):
    evidence = {"source": "/v2/suspensions/", "checked_through": checked_through,
                "window": {"first_session": "2026-08-11",
                           "last_session": checked_through, "sessions": 10}}
    if price:
        evidence["price"] = price
    return {"warning_id": wid, "resolved_on": resolved_on, "outcome": "false_positive",
            "days_elapsed": days, "evidence": evidence}


def still_open(wid, resolved_on="2026-09-10"):
    return {"warning_id": wid, "resolved_on": resolved_on, "outcome": "still_open",
            "days_elapsed": 2,
            "evidence": {"source": "/v2/suspensions/", "checked_through": resolved_on,
                         "sessions_remaining": 8}}


def expired(wid, resolved_on="2026-09-20"):
    return {"warning_id": wid, "resolved_on": resolved_on, "outcome": "expired",
            "days_elapsed": 10,
            "evidence": {"source": "/v2/suspensions/", "checked_through": "2026-09-04",
                         "corpus_fresh_through": "2026-09-04"}}


@pytest.fixture
def state(tmp_path):
    """Three temp paths. The real `state/` is never opened by this file."""
    return (str(tmp_path / "warnings.jsonl"), str(tmp_path / "outcomes.jsonl"),
            str(tmp_path / "lessons.jsonl"))


def corpus(tmp_path, rows=()):
    """A recording that names a subsector for a symbol, in the two payload shapes."""
    root = tmp_path / "recorded"
    root.mkdir(exist_ok=True)
    manifest = {}
    for path, params, payload in rows:
        key = cache_mod.slug(path, params)
        manifest[key] = {"path": path, "params": params or {}, "status": 200,
                         "est_cost": 1, "fetched_at": 0}
        (root / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
    (root / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return cache_mod.Cache(root=str(root))


def write(warnings_path, outcomes_path, warnings=(), outcomes=()):
    for row in warnings:
        ledger.append_warning(row, path=warnings_path)
    for row in outcomes:
        ledger.append_outcome(row, path=outcomes_path)


# --- the three tests task 16 names ------------------------------------------
def test_every_settled_outcome_becomes_exactly_one_lesson(state):
    """One in, one out — and a retried tick writes nothing at all."""
    warnings_path, outcomes_path, lessons_path = state
    write(warnings_path, outcomes_path,
          warnings=[warning("w-20260828-ASLI", "ASLI", "2026-08-28"),
                    warning("w-20260810-PACK", "PACK", "2026-08-10")],
          outcomes=[hit("w-20260828-ASLI"), miss("w-20260810-PACK")])

    rows, skipped = lessons.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                                outcomes_path=outcomes_path, lessons_path=lessons_path)

    assert len(rows) == 2
    assert skipped == []
    on_disk = ledger.read_lessons(lessons_path)
    assert [r["warning_id"] for r in on_disk] == ["w-20260828-ASLI", "w-20260810-PACK"]

    before = open(lessons_path, "rb").read()
    again, _skipped = lessons.run(today=date(2026, 9, 11), warnings_path=warnings_path,
                                  outcomes_path=outcomes_path,
                                  lessons_path=lessons_path)
    assert again == []
    assert open(lessons_path, "rb").read() == before


def test_a_lesson_carries_all_six_fields_and_none_are_empty(tmp_path, state):
    """§4's six, filled from the two rows that already exist. No blanks."""
    warnings_path, outcomes_path, lessons_path = state
    source = corpus(tmp_path, [
        ("/v2/company/report/ASLI/", {"sections": "overview"},
         {"symbol": "ASLI.JK", "overview": {"sub_sector": "Basic Materials"}}),
    ])
    write(warnings_path, outcomes_path,
          warnings=[warning("w-20260828-ASLI", "ASLI", "2026-08-28"),
                    warning("w-20260810-PACK", "PACK", "2026-08-10")],
          outcomes=[hit("w-20260828-ASLI"),
                    miss("w-20260810-PACK",
                         price={"from": "2026-08-11", "through": "2026-08-24",
                                "change_pct": -18.5, "sessions_without_trade": 2})])

    rows, _skipped = lessons.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                                 outcomes_path=outcomes_path,
                                 lessons_path=lessons_path, cache=source)

    six = ("conditions", "expected", "actual", "hypothesis", "axis_implicated",
           "subsector")
    for row in rows:
        for field in six:
            assert row[field], f"{row['warning_id']}: field {field} kosong"
            assert str(row[field]).strip()
    by_id = {row["warning_id"]: row for row in rows}

    lesson = by_id["w-20260828-ASLI"]
    assert lesson["subsector"] == "Basic Materials"
    assert "0.61" in lesson["conditions"] and "ambang 0.45" in lesson["conditions"]
    assert "2026-09-04" in lesson["actual"]
    assert "10 sesi bursa" in lesson["expected"]

    # The miss states how far the search reached, and what the price did.
    assert "sampai 2026-09-10" in by_id["w-20260810-PACK"]["actual"]
    assert "turun 18.5%" in by_id["w-20260810-PACK"]["actual"]

    # And the rows on disk validate against the ledger's own schema.
    assert len(ledger.read_lessons(lessons_path)) == 2


def test_recent_respects_the_window(state):
    """Step 3 hands the screen thirty days. Inclusive at the edge, nothing older."""
    _warnings_path, _outcomes_path, lessons_path = state
    for day in ("2026-09-10", "2026-08-12", "2026-08-11", "2026-07-01"):
        ledger.append_lesson(
            {"warning_id": f"w-{day.replace('-', '')}-ASLI", "written_on": day,
             "conditions": "x", "expected": "y", "actual": "z", "hypothesis": "h",
             "axis_implicated": "concentration", "subsector": "Basic Materials"},
            path=lessons_path)

    today = date(2026, 9, 10)
    kept = lessons.recent(days=30, today=today, path=lessons_path)

    # 2026-08-11 is exactly 30 days before; 2026-07-01 is 71 and must be gone.
    assert [r["written_on"] for r in kept] == ["2026-08-11", "2026-08-12", "2026-09-10"]
    assert lessons.recent(days=0, today=today, path=lessons_path) == [
        r for r in kept if r["written_on"] == "2026-09-10"]
    assert len(lessons.recent(days=None, today=today, path=lessons_path)) == 4


# --- the asymmetries the task rests on --------------------------------------
def test_a_true_positive_teaches_too(state):
    """Step 2: the right answers are evidence for a bar, not silence."""
    warnings_path, outcomes_path, lessons_path = state
    write(warnings_path, outcomes_path,
          warnings=[warning("w-20260828-ASLI", "ASLI", "2026-08-28")],
          outcomes=[hit("w-20260828-ASLI")])

    rows, _skipped = lessons.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                                 outcomes_path=outcomes_path, lessons_path=lessons_path)

    lesson, = rows
    assert lesson["outcome"] == "true_positive"
    # The hit implicates the axis that cleared its bar by the most: volume 8.2 vs
    # 3.0 is 1.73x the bar, against concentration's 0.36x.
    assert lesson["axis_implicated"] == "volume_anomaly"
    assert "sudah pada tempatnya" in lesson["hypothesis"]


def test_a_false_positive_implicates_the_thinnest_margin(state):
    """A miss blames the weakest link, because that is the bar most plausibly wrong."""
    warnings_path, outcomes_path, lessons_path = state
    axes = {
        "concentration": {"value": 0.46, "threshold": 0.45, "fired": True},
        "volume_anomaly": {"value": 8.2, "threshold": 3.0, "fired": True},
        "momentum": {"value": 0.95, "threshold": 0.90, "fired": True},
        "catalyst": {"value": 0.05, "threshold": 0.20, "fired": True},
    }
    write(warnings_path, outcomes_path,
          warnings=[warning("w-20260810-PACK", "PACK", "2026-08-10", axes=axes)],
          outcomes=[miss("w-20260810-PACK")])

    rows, _skipped = lessons.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                                 outcomes_path=outcomes_path, lessons_path=lessons_path)

    lesson, = rows
    assert lesson["axis_implicated"] == "concentration"
    assert lesson["margin"] == pytest.approx(0.01)
    assert "terlalu longgar" in lesson["hypothesis"]


def test_an_axis_that_never_fired_is_not_described_as_having_cleared_its_bar(state):
    """The nearest miss is a nearest miss. Calling it "melewati ambang" is a lie,
    and it would point task 17 at a bar that is not the thing to move."""
    warnings_path, outcomes_path, lessons_path = state
    dark = {
        "concentration": {"value": 0.30, "threshold": 0.45, "fired": False},
        "volume_anomaly": {"value": 1.4, "threshold": 5.0, "fired": False},
        "momentum": {"value": 50, "threshold": 90, "fired": False},
        "catalyst": {"value": None, "threshold": None, "fired": None},
    }
    write(warnings_path, outcomes_path,
          warnings=[warning("w-20260810-PACK", "PACK", "2026-08-10", axes=dark,
                            fired=0)],
          outcomes=[miss("w-20260810-PACK")])

    rows, _skipped = lessons.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                                 outcomes_path=outcomes_path, lessons_path=lessons_path)

    lesson, = rows
    assert lesson["axis_implicated"] == "concentration"   # nearest to its bar
    assert "tidak menyala" in lesson["hypothesis"]
    assert "melewati" not in lesson["hypothesis"]
    assert "kombinasi sumbu" in lesson["hypothesis"]


def test_catalyst_margin_is_read_downwards(state):
    """The one axis whose bar is read the other way must not look like a miss."""
    axes = {
        "concentration": {"value": 0.90, "threshold": 0.45, "fired": True},
        "volume_anomaly": {"value": 9.0, "threshold": 3.0, "fired": True},
        "momentum": {"value": 0.99, "threshold": 0.90, "fired": True},
        # 0.02 under a 0.20 bar: fired, and 0.18 past it, not -0.18.
        "catalyst": {"value": 0.02, "threshold": 0.20, "fired": True},
    }
    assert lessons.margin("catalyst", axes["catalyst"]) == pytest.approx(0.18)
    assert lessons.margin("volume_anomaly", axes["volume_anomaly"]) == pytest.approx(6.0)


def test_an_unfinished_or_unseeable_window_writes_no_lesson(state):
    """`still_open` has no `actual` yet; `expired` would blame an axis for a blind spot."""
    warnings_path, outcomes_path, lessons_path = state
    write(warnings_path, outcomes_path,
          warnings=[warning("w-20260908-TMPO", "TMPO", "2026-09-08"),
                    warning("w-20260901-PACK", "PACK", "2026-09-01")],
          outcomes=[still_open("w-20260908-TMPO"), expired("w-20260901-PACK")])

    rows, skipped = lessons.run(today=date(2026, 9, 20), warnings_path=warnings_path,
                                outcomes_path=outcomes_path, lessons_path=lessons_path)

    assert rows == []
    assert ledger.read_lessons(lessons_path) == []
    # Declined out loud, not dropped: the tick can say why it learned nothing.
    assert [wid for wid, _reason in skipped] == ["w-20260901-PACK"]
    assert "expired" in skipped[0][1]


def test_subsector_comes_from_a_payload_that_was_paid_for(tmp_path):
    """Both payload shapes, both spellings, one bucket. No guessing a sector."""
    source = corpus(tmp_path, [
        # Nested: the ticker is at the top, `sub_sector` one level down.
        ("/v2/company/report/ANTM/", {"sections": "overview"},
         {"symbol": "ANTM.JK", "overview": {"sub_sector": "Basic Materials"}}),
        # Flat, and slugged: filings rows carry both keys side by side.
        ("/v2/filings/", {"symbol": "SRTG"},
         [{"symbol": "SRTG.JK", "sub_sector": "holding-investment-companies"}]),
    ])

    assert lessons.subsector("ANTM", cache=source) == "Basic Materials"
    assert lessons.subsector("SRTG.JK", cache=source) == "Holding Investment Companies"
    # A symbol no paid-for payload names gets an answer, not an empty string.
    assert lessons.subsector("NOPE", cache=source) == lessons.SUBSECTOR_UNKNOWN


def test_three_spellings_of_one_subsector_land_in_one_bucket(tmp_path):
    """The recording really does spell this field three ways. Three buckets would
    split the evidence task 17 counts into thirds."""
    source = corpus(tmp_path, [
        ("/v2/company/report/ADRO/", {"sections": "overview"},
         {"symbol": "ADRO.JK", "overview": {"sub_sector": "Oil, Gas & Coal"}}),
        ("/v2/filings/", {"symbol": "AKRA"},
         [{"symbol": "AKRA.JK", "sub_sector": "oil-gas-coal"}]),
        ("/v2/news/", {"symbols": "RGAS"},
         [{"symbol": "RGAS.JK", "sub_sector": "OIL, GAS & COAL"}]),
    ])

    table = lessons.subsector_map(cache=source)
    assert set(table.values()) == {"Oil, Gas & Coal"}
    assert lessons.subsector_key("Oil, Gas & Coal") == lessons.subsector_key("oil-gas-coal")


def test_a_billed_404_does_not_name_a_subsector(tmp_path):
    """A settled 404 proves the lookup ran, not that the ticker means anything."""
    root = tmp_path / "recorded"
    root.mkdir()
    key = cache_mod.slug("/v2/company/report/ZZZZ/", {"sections": "overview"})
    (root / "_manifest.json").write_text(json.dumps({
        key: {"path": "/v2/company/report/ZZZZ/", "params": {"sections": "overview"},
              "status": 404, "est_cost": 1, "fetched_at": 0}}), encoding="utf-8")

    source = cache_mod.Cache(root=str(root))
    assert lessons.subsector_map(cache=source) == {}


def test_aggregation_splits_by_axis_and_by_subsector(state):
    """Task 17's input: N per axis, and per axis within a subsector."""
    warnings_path, outcomes_path, lessons_path = state
    thin = {
        "concentration": {"value": 0.46, "threshold": 0.45, "fired": True},
        "volume_anomaly": {"value": 8.2, "threshold": 3.0, "fired": True},
        "momentum": {"value": 0.95, "threshold": 0.90, "fired": True},
        "catalyst": {"value": 0.05, "threshold": 0.20, "fired": True},
    }
    write(warnings_path, outcomes_path,
          warnings=[warning("w-20260810-PACK", "PACK", "2026-08-10", axes=thin),
                    warning("w-20260811-LIFE", "LIFE", "2026-08-11", axes=thin),
                    warning("w-20260828-ASLI", "ASLI", "2026-08-28")],
          outcomes=[miss("w-20260810-PACK"), miss("w-20260811-LIFE"),
                    hit("w-20260828-ASLI")])

    lessons.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                outcomes_path=outcomes_path, lessons_path=lessons_path)
    totals = lessons.aggregate(days=30, today=date(2026, 9, 10), path=lessons_path)

    assert totals["lessons"] == 3
    assert totals["by_axis"]["concentration"]["false_positive"] == 2
    assert totals["by_axis"]["concentration"]["true_positive"] == 0
    assert totals["by_axis"]["concentration"]["margin_mean_false_positive"] == (
        pytest.approx(0.01))
    assert totals["by_axis"]["volume_anomaly"]["true_positive"] == 1
    # Every symbol here is outside the (empty) recording, so all three share the
    # unknown bucket — the split is by key, not by how many keys there happen to be.
    assert totals["by_subsector"][lessons.SUBSECTOR_UNKNOWN]["lessons"] == 3
    assert (totals["by_axis_subsector"][f"concentration|{lessons.SUBSECTOR_UNKNOWN}"]
            ["false_positive"] == 2)


def test_context_hands_the_screen_the_window_and_its_aggregate(state):
    """Step 3's injection point: the rows themselves plus the counts over them."""
    warnings_path, outcomes_path, lessons_path = state
    write(warnings_path, outcomes_path,
          warnings=[warning("w-20260828-ASLI", "ASLI", "2026-08-28")],
          outcomes=[hit("w-20260828-ASLI")])
    lessons.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                outcomes_path=outcomes_path, lessons_path=lessons_path)

    block = lessons.context(days=30, today=date(2026, 9, 10), path=lessons_path)

    assert block["since"] == "2026-08-11" and block["through"] == "2026-09-10"
    assert [r["warning_id"] for r in block["lessons"]] == ["w-20260828-ASLI"]
    assert block["aggregate"]["by_axis"]["volume_anomaly"]["true_positive"] == 1
    assert "volume_anomaly" in lessons.render_context(block)


def test_a_lesson_without_its_warning_is_declined_not_invented(state):
    """An outcome whose warning is missing yields no lesson and says so."""
    warnings_path, outcomes_path, lessons_path = state
    write(warnings_path, outcomes_path, outcomes=[hit("w-20260828-GONE")])

    rows, skipped = lessons.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                                outcomes_path=outcomes_path, lessons_path=lessons_path)

    assert rows == []
    assert skipped == [("w-20260828-GONE", "peringatannya tidak ada di warnings.jsonl")]


def test_dry_run_writes_nothing(state):
    warnings_path, outcomes_path, lessons_path = state
    write(warnings_path, outcomes_path,
          warnings=[warning("w-20260828-ASLI", "ASLI", "2026-08-28")],
          outcomes=[hit("w-20260828-ASLI")])

    rows, _skipped = lessons.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                                 outcomes_path=outcomes_path,
                                 lessons_path=lessons_path, dry_run=True)

    assert len(rows) == 1
    assert ledger.read_lessons(lessons_path) == []
