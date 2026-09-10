"""What the SETEL step must never do: move a bar it cannot justify.

Task 17 names five tests, and each one guards a different way this layer turns
into overfitting presented as insight:

  * **a shift larger than a tenth is refused.** Not clamped — a proposal nobody
    computed must not be silently shrunk into a legal one and then applied.
  * **an axis with three settled events does not move.** `yunus-0x/meridian` moves
    after five; the whole argument of `riset/red-team.md` §A3 is that five, or
    three, is a sample of noise in this domain.
  * **a bar never leaves its floor or ceiling.** Without the fence the loop drifts
    to one of the two useless states: warn about everything, or never warn.
  * **`--reset` returns exactly to version 1.** A loop that cannot be switched off
    is not one to run unattended.
  * **the hold-out is never read by the tuning path.** This is the one that makes
    every number in the video defensible, so it is tested structurally: the
    hold-out slice is replaced wholesale and the decision must not budge.

Zero credits: every corpus below is a list of dicts and a JSON file in `tmp_path`.
No client is constructed anywhere in this file, and `evolve` imports none.
"""
import json

import pytest

from app import ledger
from app.agent import evolve


# --- fixtures ---------------------------------------------------------------
def lesson(wid, axis="concentration", outcome="false_positive", margin=0.02,
           subsector="perbankan", written_on="2026-09-10"):
    """One `lessons.jsonl` row, valid against `ledger.LESSON_SCHEMA`."""
    return {
        "warning_id": wid, "written_on": written_on,
        "conditions": "konsentrasi 0,42 terhadap ambang 0,40 — menyala",
        "expected": ledger.PREDICTION,
        "actual": "tidak ada suspensi dalam 10 sesi",
        "hypothesis": "ambang konsentrasi mungkin masih terlalu longgar",
        "axis_implicated": axis, "subsector": subsector,
        "outcome": outcome, "margin": margin,
    }


def series(count, day_from, axis="concentration", outcome="false_positive",
           margin=0.02, month=3, symbol="AAA"):
    """`count` lessons on consecutive dated ids, so each has its own warning_id."""
    return [lesson(f"w-2026{month:02d}{day_from + i:02d}-{symbol}", axis=axis,
                   outcome=outcome, margin=margin)
            for i in range(count)]


def tuning_corpus(hits=12, misses=10, hit_margin=0.10, miss_margin=0.02):
    """22 settled lessons before the hold-out boundary, margins that separate.

    Misses clear the bar by 0,02 on average and hits by 0,10, so a bar moved a
    little upward removes misses first — the separation `propose()` looks for.
    """
    return (series(misses, 1, outcome="false_positive", margin=miss_margin, month=3)
            + series(hits, 1, outcome="true_positive", margin=hit_margin, month=4))


def holdout_corpus(kind="better"):
    """Four hold-out lessons dated after the boundary. Never allowed to tune."""
    survives, dies = ("true_positive", "false_positive") if kind == "better" \
        else ("false_positive", "true_positive")
    return (series(2, 1, outcome=survives, margin=0.20, month=8, symbol="ZZB")
            + series(2, 3, outcome=dies, margin=0.005, month=8, symbol="ZZD"))


def thresholds_doc(**overrides):
    """A version-1 document whose bars were all set by hand. The reset target."""
    doc = {
        "version": 1,
        "updated_on": "2026-09-01",
        "current": {"concentration": 0.40, "volume_anomaly": 5.0},
        "bounds": {"concentration": {"floor": 0.30, "ceiling": 0.75},
                   "volume_anomaly": {"floor": 2.0, "ceiling": 25.0}},
        "history": [
            {"version": 1, "on": "2026-09-01", "axis": "concentration",
             "from": None, "to": 0.40, "reason": "nilai awal", "source": "bootstrap"},
            {"version": 1, "on": "2026-09-01", "axis": "volume_anomaly",
             "from": None, "to": 5.0, "reason": "nilai awal", "source": "bootstrap"},
        ],
    }
    doc.update(overrides)
    return doc


@pytest.fixture
def thresholds_path(tmp_path):
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps(thresholds_doc()), encoding="utf-8")
    return str(path)


def only(decisions, axis="concentration"):
    matched = [d for d in decisions if d.proposal.axis == axis]
    assert matched, f"tidak ada keputusan untuk sumbu {axis}"
    return matched[0]


def guard(decision, name):
    matched = [g for g in decision.guards if g.name == name]
    assert matched, f"pagar {name} tidak dijalankan"
    return matched[0]


# --- the split --------------------------------------------------------------
def test_a_warning_is_dated_by_its_own_id_not_by_when_the_lesson_was_written():
    """`written_on` is when the replay ran; the id is when the warning was issued."""
    assert evolve.warning_date("w-20260312-ASLI").isoformat() == "2026-03-12"
    assert evolve.warning_date("w-20261332-ASLI") is None      # month 13
    assert evolve.warning_date("bukan-id") is None
    assert evolve.warning_date(None) is None


def test_an_undatable_lesson_is_dropped_rather_than_assumed_historical():
    rows = [lesson("w-20260312-ASLI"), lesson("tanpa-tanggal")]
    split = evolve.split_lessons(rows)
    assert len(split[evolve.TUNING]) == 1
    assert split[evolve.HOLDOUT] == []


# --- guard 1: N minimum -------------------------------------------------------
def test_an_axis_with_three_settled_events_does_not_move(thresholds_path):
    """Three is what `yunus-0x/meridian`-style tuning would act on. Here it is noise."""
    rows = series(3, 1, outcome="false_positive", margin=0.02, month=3)
    _split, decisions, _doc = evolve.plan(lessons=rows,
                                          thresholds_path=thresholds_path)
    decision = only(decisions)
    assert decision.proposal.n == 3
    assert guard(decision, "n_minimum").passed is False
    assert decision.allowed is False

    evolve.run(lessons=rows, thresholds_path=thresholds_path)
    after = ledger.load_thresholds(thresholds_path)
    assert after["current"]["concentration"] == 0.40
    assert after["version"] == 1


def test_lessons_from_the_holdout_side_do_not_count_toward_the_minimum(thresholds_path):
    """25 events, all after the boundary. N in the tuning set is still zero."""
    rows = (series(13, 1, outcome="false_positive", margin=0.02, month=8)
            + series(12, 1, outcome="true_positive", margin=0.10, month=9,
                     symbol="BBB"))
    split, decisions, _doc = evolve.plan(lessons=rows,
                                         thresholds_path=thresholds_path)
    assert len(split[evolve.HOLDOUT]) == 25
    assert split[evolve.TUNING] == []
    assert decisions == []


# --- guard 2: the step cap ----------------------------------------------------
def test_a_shift_larger_than_a_tenth_is_refused_not_clamped(thresholds_path):
    """The guard is a gate. Shrinking an over-large proposal would apply a
    movement nobody computed, and the history would cite reasoning for a number
    that never came out of it."""
    doc = ledger.load_thresholds(thresholds_path)
    proposal = evolve.Proposal(
        axis="concentration", current=0.40, proposed=0.50, delta=0.10, n=40,
        true_positive=20, false_positive=20, margin_true_positive=0.10,
        margin_false_positive=0.20, separation=-0.10,
        evidence=("w-20260312-ASLI",), rationale="usulan dari luar")
    holdout = evolve.holdout_numbers(proposal, holdout_corpus())
    guards = evolve.check_guards(proposal, doc, holdout)
    step = [g for g in guards if g.name == "batas_langkah"][0]
    assert step.passed is False
    assert "25.0%" in step.detail

    decision = evolve.Decision(proposal=proposal, holdout=holdout, guards=guards)
    assert decision.allowed is False
    assert "batas_langkah" in decision.refusal()


def test_a_proposal_this_module_makes_is_always_inside_the_step_cap(thresholds_path):
    """The proposer caps itself, so guard 2 is a backstop and not the brake."""
    doc = ledger.load_thresholds(thresholds_path)
    # Misses clear the bar by a mile: an uncapped step would be 0,5 x 0,90.
    rows = (series(11, 1, outcome="false_positive", margin=0.90, month=3)
            + series(11, 1, outcome="true_positive", margin=2.00, month=4))
    proposal = evolve.propose(rows, doc)[0]
    assert proposal.fraction <= evolve.MAX_STEP_FRACTION + 1e-12
    assert proposal.delta == pytest.approx(evolve.MAX_STEP_FRACTION * 0.40)
    assert "dipotong batas langkah" in proposal.rationale


# --- guard 3: floor and ceiling ----------------------------------------------
def test_a_bar_never_leaves_the_floor_or_the_ceiling(thresholds_path):
    doc = ledger.load_thresholds(thresholds_path)
    for proposed in (0.29, 0.80):
        proposal = evolve.Proposal(axis="concentration", current=0.40,
                                   proposed=proposed, delta=abs(proposed - 0.40),
                                   n=40, evidence=("w-20260312-ASLI",))
        guards = evolve.check_guards(proposal, doc,
                                     evolve.holdout_numbers(proposal,
                                                            holdout_corpus()))
        assert [g for g in guards if g.name == "lantai_langit"][0].passed is False


def test_repeated_runs_never_walk_a_bar_past_its_ceiling(thresholds_path):
    """Ten iterations of a corpus that always says "tighter". The fence holds.

    Each run re-reads the file, so the bar compounds; without a fence a tenth per
    iteration reaches the ceiling and keeps going.
    """
    floor, ceiling = 0.30, 0.75
    for _ in range(10):
        doc = ledger.load_thresholds(thresholds_path)
        bar = doc["current"]["concentration"]
        rows = (series(11, 1, outcome="false_positive", margin=bar * 0.5, month=3)
                + series(11, 1, outcome="true_positive", margin=bar * 2, month=4))
        evolve.run(lessons=rows + holdout_corpus(),
                   thresholds_path=thresholds_path, on="2026-09-11")
        value = ledger.load_thresholds(thresholds_path)["current"]["concentration"]
        assert floor <= value <= ceiling


# --- guard 4: the hold-out reports, it does not select -------------------------
def test_the_tuning_path_never_reads_the_holdout_slice(thresholds_path):
    """The same tuning lessons with two opposite hold-out slices decide the same.

    `better` and `worse` invert every hold-out outcome, so the reported precision
    moves from 0,5 -> 1,0 to 0,5 -> 0,0. If the hold-out were feeding the decision
    in any way — as a tie-break, as a veto, as a scale — these two runs would
    differ. They must not.
    """
    tuning = tuning_corpus()
    outcomes = {}
    for kind in ("better", "worse"):
        _split, decisions, _doc = evolve.plan(lessons=tuning + holdout_corpus(kind),
                                              thresholds_path=thresholds_path)
        decision = only(decisions)
        outcomes[kind] = (decision.proposal, decision.allowed)

    assert outcomes["better"][0] == outcomes["worse"][0]
    assert outcomes["better"][1] is outcomes["worse"][1] is True


def test_a_shift_that_worsens_the_holdout_is_applied_and_reported(thresholds_path):
    """§Jangan: do not hide it when the self-tuning bar loses. Print it, keep it."""
    rows = tuning_corpus() + holdout_corpus("worse")
    _split, decisions, _doc = evolve.run(lessons=rows,
                                         thresholds_path=thresholds_path, on="2026-09-11")
    decision = only(decisions)
    assert decision.applied is True
    assert decision.holdout.before == 0.5
    assert decision.holdout.after == 0.0
    assert decision.holdout.improved is False
    assert "turun" in decision.reason()
    assert "hold-out tidak dipakai memilih" in decision.reason()


def test_an_axis_with_no_holdout_lessons_does_not_move(thresholds_path):
    """No number to report about the change means the change is not reviewable."""
    _split, decisions, _doc = evolve.plan(lessons=tuning_corpus(),
                                          thresholds_path=thresholds_path)
    decision = only(decisions)
    assert decision.holdout.computable is False
    assert guard(decision, "hold_out").passed is False
    assert decision.allowed is False


def test_a_proposal_that_silences_every_holdout_warning_does_not_move(thresholds_path):
    """Survivors of zero leave no precision to compute, so there is nothing to say."""
    rows = tuning_corpus() + series(4, 1, outcome="false_positive", margin=0.001,
                                    month=8, symbol="ZZS")
    _split, decisions, _doc = evolve.plan(lessons=rows,
                                          thresholds_path=thresholds_path)
    decision = only(decisions)
    assert decision.holdout.n_before == 4
    assert decision.holdout.n_after == 0
    assert guard(decision, "hold_out").passed is False
    assert decision.allowed is False


# --- what an applied change records -------------------------------------------
def test_an_applied_change_bumps_the_version_and_records_its_own_evidence(
        thresholds_path):
    rows = tuning_corpus() + holdout_corpus()
    _split, decisions, doc = evolve.run(lessons=rows,
                                        thresholds_path=thresholds_path,
                                        on="2026-09-11")
    decision = only(decisions)
    assert decision.applied is True
    assert doc["version"] == 2
    assert doc["current"]["concentration"] == pytest.approx(0.41)

    entry = doc["history"][-1]
    assert entry["version"] == 2
    assert entry["on"] == "2026-09-11"
    assert entry["axis"] == "concentration"
    assert entry["from"] == 0.40
    assert entry["to"] == pytest.approx(0.41)
    assert entry["source"] == "evolve"
    assert entry["n_resolved"] == 22
    assert entry["holdout_before"] == 0.5
    assert entry["holdout_after"] == 1.0
    assert len(entry["evidence"]) == 22
    assert entry["reason"].strip()
    # The file it wrote is still a file the ledger will accept.
    ledger.validate_thresholds(ledger.load_thresholds(thresholds_path))


def test_an_axis_whose_margins_do_not_separate_is_reported_not_moved(thresholds_path):
    """Misses clear the bar by more than hits do. Tightening would cost hits first."""
    rows = tuning_corpus(hit_margin=0.02, miss_margin=0.10) + holdout_corpus()
    _split, decisions, _doc = evolve.plan(lessons=rows,
                                          thresholds_path=thresholds_path)
    decision = only(decisions)
    assert decision.proposal.n == 22
    assert guard(decision, "n_minimum").passed is True
    assert decision.proposal.delta == 0
    assert decision.allowed is False
    assert "tidak memisahkan" in decision.proposal.rationale


# --- guard 5: the kill switch --------------------------------------------------
def test_reset_returns_the_bars_exactly_to_version_one(thresholds_path):
    before = ledger.load_thresholds(thresholds_path)
    assert before["version"] == 1
    original = dict(before["current"])

    rows = tuning_corpus() + holdout_corpus()
    for day in ("2026-09-11", "2026-09-12"):
        evolve.run(lessons=rows, thresholds_path=thresholds_path, on=day)
    moved = ledger.load_thresholds(thresholds_path)
    assert moved["current"]["concentration"] != original["concentration"]

    changes, after = evolve.reset(thresholds_path=thresholds_path, on="2026-09-13")
    assert changes == {"concentration": original["concentration"]}
    assert after["current"] == original
    assert ledger.reconstruct(after, 1)["current"] == original


def test_reset_goes_forward_so_the_undone_changes_stay_on_the_record(thresholds_path):
    """A kill switch nobody can see was pressed is not an auditable one."""
    rows = tuning_corpus() + holdout_corpus()
    evolve.run(lessons=rows, thresholds_path=thresholds_path, on="2026-09-11")
    _changes, after = evolve.reset(thresholds_path=thresholds_path, on="2026-09-13")

    assert after["version"] == 3
    assert [e["source"] for e in after["history"]][-2:] == ["evolve", "rollback"]
    assert "reset ke nilai awal" in after["history"][-1]["reason"]


def test_reset_leaves_bars_a_human_set_alone(thresholds_path):
    """Undo the machine, not the team. On a hand-set document it changes nothing."""
    ledger.record_change({"volume_anomaly": 6.0}, reason="disetel tangan",
                         on="2026-09-11", source="bootstrap", path=thresholds_path)
    changes, doc = evolve.reset(thresholds_path=thresholds_path, on="2026-09-12")
    assert changes == {}
    assert doc["current"]["volume_anomaly"] == 6.0
    assert doc["version"] == 2


def test_reset_undoes_only_the_evolved_axis(thresholds_path):
    """One axis moved by evolve, one by hand. Only the first comes back."""
    rows = tuning_corpus() + holdout_corpus()
    evolve.run(lessons=rows, thresholds_path=thresholds_path, on="2026-09-11")
    ledger.record_change({"volume_anomaly": 6.0}, reason="disetel tangan",
                         on="2026-09-12", source="bootstrap", path=thresholds_path)

    _changes, doc = evolve.reset(thresholds_path=thresholds_path, on="2026-09-13")
    assert doc["current"]["concentration"] == 0.40
    assert doc["current"]["volume_anomaly"] == 6.0


# --- the CLI --------------------------------------------------------------------
def test_the_dry_run_writes_nothing(thresholds_path, capsys):
    rows = tuning_corpus() + holdout_corpus()
    before = open(thresholds_path, encoding="utf-8").read()
    _split, decisions, _doc = evolve.run(lessons=rows,
                                         thresholds_path=thresholds_path,
                                         dry_run=True)
    assert only(decisions).allowed is True
    assert only(decisions).applied is False
    assert open(thresholds_path, encoding="utf-8").read() == before


def test_the_render_names_every_guard_and_the_split(thresholds_path):
    rows = tuning_corpus() + holdout_corpus("worse")
    split, decisions, doc = evolve.plan(lessons=rows,
                                        thresholds_path=thresholds_path)
    text = evolve.render(split, decisions, doc, "2026-07-01", dry_run=True)
    for name in evolve.GUARD_NAMES:
        assert name in text
    assert "hold-out" in text
    assert "hold-out TIDAK membaik" in text
