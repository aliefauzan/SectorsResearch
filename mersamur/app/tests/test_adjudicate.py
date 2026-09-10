"""What the NILAI step must never do: invent a miss, or write one twice.

Task 15's three named tests are here, and each of them is aimed at a failure that
would show up in the file a judge opens rather than in a stack trace:

  * **a second opinion.** The scheduler retries. If a retry appends a second row
    for the same warning, `outcomes.jsonl` stops being a record of decisions and
    becomes a record of how many times cron fired. `test_running_twice_...` compares
    the bytes.
  * **a premature miss.** A warning whose ten sessions have not elapsed is a
    prediction in flight, not a wrong one. `test_unfinished_window_...` checks both
    halves: the outcome is `still_open`, and `ledger.open_warnings` still returns it.
  * **an unevidenced hit.** A `true_positive` is the product's whole claim, so it
    has to arrive with the announcement's date, its class and its `pdf_url`.

Two more cover the distinction the task is built on: a finished window the label
source cannot see is `expired`, not `false_positive`, and the suspension read
happens once per tick however many warnings are open.

Zero credits: every corpus below is three files in `tmp_path`. No client is ever
constructed, so nothing here can open a socket.
"""
import json
from datetime import date, datetime

import pytest

from app import cache as cache_mod, ledger
from app.agent import adjudicate


# --- corpus fixtures --------------------------------------------------------
def stamp(day):
    """A `fetched_at` for `day`, at noon so no timezone can move it to the 9th."""
    return datetime(day.year, day.month, day.day, 12, 0).timestamp()


def suspension(symbol, day, reason=None, pdf_url="https://www.idx.co.id/x.pdf"):
    """One announcement row, in `/v2/suspensions/`' own field names."""
    return {
        "symbol": f"{symbol}.JK",
        "suspension_date": day,
        # The wording that 18 of the 20 most recent real rows carry, so
        # `labels.classify` sees the class it actually has to recognise.
        "reason": reason or (f"Terjadinya peningkatan harga kumulatif yang signifikan "
                             f"pada saham {symbol}.JK, dalam rangka cooling down sebagai "
                             f"bentuk perlindungan bagi investor"),
        "pdf_url": pdf_url,
    }


# The corpus reaches back only as far as its oldest row, which is exactly true of a
# single `/v2/suspensions/` page. Tests that want a window to be *judged* rather
# than reported unseeable have to anchor the corpus before that window.
ANCHOR = ("ANCH", "2026-07-01")


def corpus(tmp_path, rows=(), fresh_on=date(2026, 9, 10), daily=None, anchor=True):
    """A three-file recording: manifest, suspension payload, optional daily payload.

    Built rather than reused so the temporal bounds under test are the ones the
    test set, not whatever the shipped archive happens to hold today.
    """
    rows = list(rows)
    if anchor:
        rows.append(suspension(*ANCHOR))
    root = tmp_path / "recorded"
    root.mkdir(exist_ok=True)
    manifest = {}

    key = cache_mod.slug(adjudicate.SUSPENSION_SOURCE, adjudicate.SUSPENSION_PARAMS)
    manifest[key] = {"path": adjudicate.SUSPENSION_SOURCE,
                     "params": dict(adjudicate.SUSPENSION_PARAMS),
                     "status": 200, "est_cost": 20, "fetched_at": stamp(fresh_on)}
    (root / f"{key}.json").write_text(
        json.dumps({"results": list(rows), "pagination": {"total_count": len(rows)}}),
        encoding="utf-8")

    for symbol, sessions in (daily or {}).items():
        path = f"/v2/daily/{symbol}/"
        dkey = cache_mod.slug(path, {})
        manifest[dkey] = {"path": path, "params": {}, "status": 200, "est_cost": 1,
                          "fetched_at": stamp(fresh_on)}
        (root / f"{dkey}.json").write_text(json.dumps(sessions), encoding="utf-8")

    (root / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return cache_mod.Cache(root=str(root))


class CountingCache(cache_mod.Cache):
    """A cache that remembers how many times the label source was read."""

    def __init__(self, root):
        super().__init__(root=root)
        self.suspension_reads = 0

    def get(self, path, params=None, method="GET"):
        if path == adjudicate.SUSPENSION_SOURCE:
            self.suspension_reads += 1
        return super().get(path, params, method)


def warning(wid, symbol, day):
    """A four-axis warning row. Only its id, symbol and date matter to this step."""
    return {
        "id": wid, "symbol": symbol, "date": day,
        "axes": {axis: {"value": 0.5, "threshold": 0.4, "fired": True}
                 for axis in ("concentration", "volume_anomaly", "momentum", "catalyst")},
        "axes_fired": 4, "axes_total": 4, "thresholds_version": 3,
        "prediction": ledger.PREDICTION, "credits_spent": 4, "status": "open",
    }


@pytest.fixture
def state(tmp_path):
    """`(warnings_path, outcomes_path)` in a temp directory. Real state is untouched."""
    return str(tmp_path / "warnings.jsonl"), str(tmp_path / "outcomes.jsonl")


def write(warnings_path, *rows):
    for row in rows:
        ledger.append_warning(row, path=warnings_path)


# --- the three tests task 15 names ------------------------------------------
def test_running_twice_leaves_outcomes_byte_identical(tmp_path, state):
    """A retried tick must be a no-op, including for the non-terminal note."""
    warnings_path, outcomes_path = state
    write(warnings_path,
          warning("w-20260828-ASLI", "ASLI", "2026-08-28"),    # resolves
          warning("w-20260908-TMPO", "TMPO", "2026-09-08"))    # still in flight
    source = corpus(tmp_path, [suspension("ASLI", "2026-09-04")])

    first = adjudicate.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                           outcomes_path=outcomes_path, cache=source)
    assert len(first[2]) == 2
    before = open(outcomes_path, "rb").read()

    second = adjudicate.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                            outcomes_path=outcomes_path, cache=source)
    assert second[2] == []
    assert open(outcomes_path, "rb").read() == before
    assert all(v.duplicate for v in second[1])


def test_unfinished_window_stays_open_and_is_never_a_miss(tmp_path, state):
    """The rule task 15 is most emphatic about: in flight is not failed."""
    warnings_path, outcomes_path = state
    write(warnings_path, warning("w-20260908-TMPO", "TMPO", "2026-09-08"))
    source = corpus(tmp_path)

    _corpus, verdicts, _written = adjudicate.run(
        today=date(2026, 9, 10), warnings_path=warnings_path,
        outcomes_path=outcomes_path, cache=source)

    assert [v.outcome for v in verdicts] == ["still_open"]
    verdict = verdicts[0]
    assert not verdict.terminal
    assert verdict.evidence["sessions_remaining"] > 0
    assert verdict.evidence["checked_through"] == "2026-09-10"
    # The warning is still the adjudicator's business tomorrow.
    still = ledger.open_warnings(warnings_path=warnings_path, outcomes_path=outcomes_path)
    assert [row["id"] for row in still] == ["w-20260908-TMPO"]


def test_true_positive_carries_a_dated_sourced_announcement(tmp_path, state):
    """Every hit has to be checkable by a judge, which means a date and a link."""
    warnings_path, outcomes_path = state
    write(warnings_path, warning("w-20260828-ASLI", "ASLI", "2026-08-28"))
    pdf = "https://www.idx.co.id/Portals/0/x/20260903-WAS_Suspensi_ASLI.pdf"
    source = corpus(tmp_path, [suspension("ASLI", "2026-09-04", pdf_url=pdf)])

    _corpus, verdicts, _written = adjudicate.run(
        today=date(2026, 9, 10), warnings_path=warnings_path,
        outcomes_path=outcomes_path, cache=source)

    verdict, = verdicts
    assert verdict.outcome == "true_positive"
    assert verdict.evidence["source"] == "/v2/suspensions/"
    assert verdict.evidence["suspension_date"] == "2026-09-04"
    assert verdict.evidence["reason_class"] == "cooling_down"
    assert verdict.evidence["pdf_url"] == pdf
    # 2026-08-28 -> 2026-09-04, in calendar days.
    assert verdict.days_elapsed == 7
    # And the row that reached disk says the same thing.
    row, = ledger.read_outcomes(outcomes_path)
    assert row["evidence"]["pdf_url"] == pdf


# --- the distinction the four outcomes rest on ------------------------------
def test_finished_covered_window_with_nothing_in_it_is_a_false_positive(tmp_path, state):
    warnings_path, outcomes_path = state
    write(warnings_path, warning("w-20260810-PACK", "PACK", "2026-08-10"))
    source = corpus(tmp_path, fresh_on=date(2026, 9, 10))

    _corpus, verdicts, _written = adjudicate.run(
        today=date(2026, 9, 10), warnings_path=warnings_path,
        outcomes_path=outcomes_path, cache=source)

    verdict, = verdicts
    assert verdict.outcome == "false_positive"
    assert verdict.terminal
    # A negative's evidence is the search that came up empty, so it has to say how
    # far that search actually reached.
    assert verdict.evidence["checked_through"] == "2026-09-10"


def test_window_the_label_source_cannot_see_is_expired_not_a_miss(tmp_path, state):
    """A stale or shallow corpus must not be able to manufacture false positives."""
    warnings_path, outcomes_path = state
    write(warnings_path, warning("w-20260901-PACK", "PACK", "2026-09-01"))
    # Read only to 4 September; the window runs to the 15th. Nothing could be seen.
    source = corpus(tmp_path, fresh_on=date(2026, 9, 4))

    _corpus, verdicts, _written = adjudicate.run(
        today=date(2026, 9, 20), warnings_path=warnings_path,
        outcomes_path=outcomes_path, cache=source)

    verdict, = verdicts
    assert verdict.outcome == "expired"
    assert verdict.evidence["corpus_fresh_through"] == "2026-09-04"
    assert verdict.evidence["window"]["last_session"] > "2026-09-04"


def test_the_label_source_is_read_once_per_tick(tmp_path, state):
    """Step 6: the tick's credit bill must not scale with the number of warnings."""
    warnings_path, outcomes_path = state
    write(warnings_path,
          warning("w-20260828-ASLI", "ASLI", "2026-08-28"),
          warning("w-20260828-LIFE", "LIFE", "2026-08-28"),
          warning("w-20260828-NICK", "NICK", "2026-08-28"),
          warning("w-20260828-TRUK", "TRUK", "2026-08-28"))
    root = corpus(tmp_path, [suspension("ASLI", "2026-09-04")]).root
    counting = CountingCache(root)

    _corpus, verdicts, _written = adjudicate.run(
        today=date(2026, 9, 10), warnings_path=warnings_path,
        outcomes_path=outcomes_path, cache=counting)

    assert len(verdicts) == 4
    assert counting.suspension_reads == 1


# --- evidence that came from prices -----------------------------------------
def test_price_evidence_is_dated_and_absent_rather_than_zero(tmp_path, state):
    """Descriptive price behaviour, or no key at all. Never zeros standing in for it."""
    warnings_path, outcomes_path = state
    write(warnings_path,
          warning("w-20260810-PACK", "PACK", "2026-08-10"),
          warning("w-20260810-SAFE", "SAFE", "2026-08-10"))
    sessions = [{"symbol": "PACK.JK", "date": "2026-08-11", "close": 100, "volume": 1000},
                {"symbol": "PACK.JK", "date": "2026-08-12", "close": 150, "volume": 2000},
                {"symbol": "PACK.JK", "date": "2026-08-13", "close": 120, "volume": 0}]
    source = corpus(tmp_path, fresh_on=date(2026, 9, 10), daily={"PACK": sessions})

    _corpus, verdicts, _written = adjudicate.run(
        today=date(2026, 9, 10), warnings_path=warnings_path,
        outcomes_path=outcomes_path, cache=source)

    by_id = {v.warning_id: v for v in verdicts}
    assert {v.outcome for v in verdicts} == {"false_positive"}
    price = by_id["w-20260810-PACK"].evidence["price"]
    assert price["source"] == "/v2/daily/PACK/"
    assert (price["from"], price["through"]) == ("2026-08-11", "2026-08-13")
    assert price["close_high"] == 150
    assert price["sessions_without_trade"] == 1
    assert price["change_pct"] == 20.0
    # SAFE has no recorded series, so the key is missing rather than zeroed.
    assert "price" not in by_id["w-20260810-SAFE"].evidence


def test_a_duplicated_warning_id_produces_exactly_one_outcome(tmp_path, state):
    """`id` is date+symbol, so the same day can append it twice. One row out."""
    warnings_path, outcomes_path = state
    write(warnings_path,
          warning("w-20260828-ASLI", "ASLI", "2026-08-28"),
          warning("w-20260828-ASLI", "ASLI", "2026-08-28"))
    source = corpus(tmp_path, [suspension("ASLI", "2026-09-04")])

    adjudicate.run(today=date(2026, 9, 10), warnings_path=warnings_path,
                   outcomes_path=outcomes_path, cache=source)

    assert len(ledger.read_outcomes(outcomes_path)) == 1


def test_dry_run_writes_nothing(tmp_path, state):
    warnings_path, outcomes_path = state
    write(warnings_path, warning("w-20260828-ASLI", "ASLI", "2026-08-28"))
    source = corpus(tmp_path, [suspension("ASLI", "2026-09-04")])

    _corpus, verdicts, written = adjudicate.run(
        today=date(2026, 9, 10), warnings_path=warnings_path,
        outcomes_path=outcomes_path, cache=source, dry_run=True)

    assert [v.outcome for v in verdicts] == ["true_positive"]
    assert written == []
    assert ledger.read_outcomes(outcomes_path) == []


def test_a_non_label_suspension_in_the_window_is_context_not_a_hit(tmp_path, state):
    """Only cooling-down is the target. A going-concern halt is a different question."""
    warnings_path, outcomes_path = state
    write(warnings_path, warning("w-20260810-PACK", "PACK", "2026-08-10"))
    source = corpus(tmp_path, [suspension("PACK", "2026-08-14",
                                          reason="Going concern")],
                    fresh_on=date(2026, 9, 10))

    _corpus, verdicts, _written = adjudicate.run(
        today=date(2026, 9, 10), warnings_path=warnings_path,
        outcomes_path=outcomes_path, cache=source)

    verdict, = verdicts
    assert verdict.outcome == "false_positive"
    assert verdict.evidence["other_suspensions"][0]["reason_class"] != "cooling_down"


def test_horizon_matches_the_backtest(tmp_path):
    """The tick and the backtest must judge over the same ten sessions."""
    from app import backtest
    assert adjudicate.HORIZON_SESSIONS == backtest.HORIZON_SESSIONS
    assert adjudicate.HORIZON_SESSIONS == ledger.PREDICTION_HORIZON_SESSIONS
