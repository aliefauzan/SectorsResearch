"""What the four state files must never do: lose a line, accept a broken one, or
lose the ability to go back.

These are the files a judge opens, so the tests are aimed at the three failures
that would make them worthless as evidence:

  * **a rewritten log.** If yesterday's warning can be edited today, no row in the
    file proves anything about prediction. `test_second_write_never_touches_the_first`
    checks the bytes, and `test_only_the_thresholds_writer_truncates` checks the
    syntax tree, because a behavioural test only covers the paths it happens to walk.
  * **a broken line.** A malformed row is worse than a missing one: it is found
    late, by the reader it was written for. Every rejection case below is a row a
    plausible caller would produce — a bool where a count belongs, a float that is
    `NaN`, a `true_positive` with no announcement behind it.
  * **a threshold that cannot be rolled back.** The evolve step (task 17) moves the
    bars automatically; the only thing that makes that safe is that every version
    can be rebuilt from the file itself. `test_every_recorded_version_can_be_rebuilt`
    proves it for the shipped document and for a synthetic multi-version one.

Zero credits: every test writes into `tmp_path` or reads
`research/harness/recorded/`. Nothing here opens a socket.
"""
import ast
import json
import math
import os
from datetime import date

import pytest

from app import backtest, ledger, profile as profile_mod


# --- fixtures ---------------------------------------------------------------
def warning(**overrides):
    """A valid warning row. Each rejection test breaks exactly one thing in it."""
    row = {
        "id": "w-20260911-ASLI",
        "symbol": "ASLI",
        "date": "2026-09-11",
        "axes": {axis: {"value": 0.5, "threshold": 0.4, "fired": True}
                 for axis in profile_mod.AXES},
        "axes_fired": 4,
        "axes_total": 4,
        "thresholds_version": 3,
        "prediction": ledger.PREDICTION,
        "credits_spent": 10,
        "status": "open",
    }
    row.update(overrides)
    return row


def outcome(**overrides):
    row = {
        "warning_id": "w-20260911-ASLI",
        "resolved_on": "2026-09-18",
        "outcome": "true_positive",
        "days_elapsed": 5,
        "evidence": {"source": "/v2/suspensions/", "suspension_date": "2026-09-16",
                     "reason_class": "cooling_down",
                     "pdf_url": "https://www.idx.co.id/contoh.pdf"},
    }
    row.update(overrides)
    return row


def lesson(**overrides):
    row = {
        "warning_id": "w-20260911-ASLI",
        "written_on": "2026-09-21",
        "conditions": "konsentrasi 0,52, volume 4,1x, tanpa katalis",
        "expected": "suspensi cooling-down dalam 10 hari bursa",
        "actual": "tidak ada suspensi; volume kembali normal dalam 3 sesi",
        "hypothesis": "konsentrasi 0,52 di bawah ambang yang berarti untuk subsektor ini",
        "axis_implicated": "concentration",
        "subsector": "Basic Materials",
    }
    row.update(overrides)
    return row


def thresholds_doc(**overrides):
    doc = {
        "version": 1,
        "updated_on": "2026-09-01",
        "current": {"concentration": 0.40, "volume_anomaly": 5.0},
        "bounds": {"concentration": {"floor": 0.30, "ceiling": 0.75},
                   "volume_anomaly": {"floor": 2.0, "ceiling": 25.0}},
        "history": [{"version": 1, "on": "2026-09-01", "axis": "concentration",
                     "from": None, "to": 0.40, "reason": "nilai awal",
                     "source": "bootstrap"}],
    }
    doc.update(overrides)
    return doc


@pytest.fixture
def thresholds_path(tmp_path):
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps(thresholds_doc()), encoding="utf-8")
    return str(path)


def log(tmp_path, name):
    return str(tmp_path / name)


# --- append-only ------------------------------------------------------------
def test_second_write_never_touches_the_first(tmp_path):
    """Two writes, and the first line is byte-identical afterwards.

    Compared as bytes rather than as parsed JSON: a writer that re-serialised the
    file would produce equal objects and a different file, and the file is the
    evidence.
    """
    path = log(tmp_path, "warnings.jsonl")
    ledger.append_warning(warning(), path=path)
    first = open(path, "rb").read()

    ledger.append_warning(warning(id="w-20260912-NICK", symbol="NICK",
                                  date="2026-09-12"), path=path)
    after = open(path, "rb").read()

    assert after.startswith(first), "baris pertama berubah setelah penulisan kedua"
    assert len(after.splitlines()) == 2
    assert [r["id"] for r in ledger.read_warnings(path)] == [
        "w-20260911-ASLI", "w-20260912-NICK"]


def test_repeated_writes_accumulate_in_order(tmp_path):
    """Ten writes leave ten lines, in the order they were decided."""
    path = log(tmp_path, "outcomes.jsonl")
    for day in range(1, 11):
        ledger.append_outcome(outcome(warning_id=f"w-2026091{day % 10}-ASLI",
                                      days_elapsed=day), path=path)
    rows = ledger.read_outcomes(path)
    assert len(rows) == 10
    assert [r["days_elapsed"] for r in rows] == list(range(1, 11))


def test_a_rejected_row_writes_nothing(tmp_path):
    """Validation happens before the file is opened, not after the line is out."""
    path = log(tmp_path, "warnings.jsonl")
    ledger.append_warning(warning(), path=path)
    before = open(path, "rb").read()

    with pytest.raises(ledger.SchemaError):
        ledger.append_warning(warning(credits_spent=-1), path=path)

    assert open(path, "rb").read() == before


def test_only_the_thresholds_writer_truncates():
    """No call in `ledger.py` may open a log for writing. Checked syntactically.

    A behavioural test only covers the code paths it walks; this one covers every
    `open()` in the module, including ones added later.
    """
    tree = ast.parse(open(ledger.__file__, encoding="utf-8").read())

    def opens(node):
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and getattr(child.func, "id", "") == "open":
                mode = "r"
                if len(child.args) > 1 and isinstance(child.args[1], ast.Constant):
                    mode = child.args[1].value
                yield mode

    truncating = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for mode in opens(node):
                assert mode in ("r", "a", "w"), f"mode open() tak dikenal: {mode!r}"
                if "w" in mode:
                    truncating.setdefault(node.name, 0)
                    truncating[node.name] += 1

    assert set(truncating) == {"_atomic_write_json"}, (
        f"hanya _atomic_write_json boleh menimpa; ditemukan juga di {sorted(truncating)}")


# --- schema at write time ---------------------------------------------------
@pytest.mark.parametrize("broken, why", [
    (warning(id="ASLI-2026-09-11"), "id bukan bentuk w-YYYYMMDD-SIMBOL"),
    (warning(date="11 September 2026"), "tanggal bukan YYYY-MM-DD"),
    (warning(credits_spent=True), "boolean lolos sebagai bilangan bulat"),
    (warning(credits_spent=-1), "kredit negatif"),
    (warning(status="ditutup"), "status di luar kosakata"),
    (warning(prediction="harga naik"), "prediksi di luar kosakata"),
    (warning(thresholds_version=None), "versi ambang null"),
    (warning(axes={"concentration": {"value": 0.5, "threshold": 0.4, "fired": True}}),
     "tidak semua sumbu hadir"),
    (warning(axes={axis: {"value": 0.5, "threshold": 0.4}
                   for axis in profile_mod.AXES}), "sumbu tanpa 'fired'"),
    (warning(axes={axis: {"value": 0.5, "threshold": 0.4, "fired": "menyala"}
                   for axis in profile_mod.AXES}), "'fired' bukan boolean/null"),
    (warning(axes_fired=float("nan")), "NaN bukan JSON"),
])
def test_warning_rows_that_must_be_refused(tmp_path, broken, why):
    with pytest.raises(ledger.SchemaError):
        ledger.append_warning(broken, path=log(tmp_path, "warnings.jsonl"))


def test_a_missing_field_is_refused(tmp_path):
    row = warning()
    del row["axes_fired"]
    with pytest.raises(ledger.SchemaError, match="axes_fired"):
        ledger.append_warning(row, path=log(tmp_path, "warnings.jsonl"))


@pytest.mark.parametrize("broken, why", [
    (outcome(outcome="mungkin"), "outcome di luar empat kelas"),
    (outcome(days_elapsed=-3), "hari berlalu negatif"),
    (outcome(evidence={"source": ""}), "bukti tanpa sumber"),
    (outcome(evidence={"source": "/v2/suspensions/",
                       "suspension_date": "2026-09-16",
                       "reason_class": "cooling_down"}),
     "true_positive tanpa pdf_url"),
    (outcome(evidence={"source": "/v2/suspensions/", "suspension_date": "kemarin",
                       "reason_class": "cooling_down", "pdf_url": ""}),
     "tanggal suspensi bukan YYYY-MM-DD"),
    (outcome(outcome="false_positive", evidence={"source": "/v2/suspensions/"}),
     "negatif tanpa checked_through"),
])
def test_outcome_rows_that_must_be_refused(tmp_path, broken, why):
    with pytest.raises(ledger.SchemaError):
        ledger.append_outcome(broken, path=log(tmp_path, "outcomes.jsonl"))


def test_a_positive_may_record_that_no_pdf_was_published(tmp_path):
    """`pdf_url` is required as a key, not as a non-empty value.

    An explicit `""` says "the announcement carried no link"; a missing key says
    nothing at all, and the difference matters to whoever checks the evidence.
    """
    row = outcome()
    row["evidence"] = dict(row["evidence"], pdf_url="")
    ledger.append_outcome(row, path=log(tmp_path, "outcomes.jsonl"))


def test_a_negative_carries_the_window_it_was_checked_through(tmp_path):
    path = log(tmp_path, "outcomes.jsonl")
    ledger.append_outcome(
        outcome(outcome="false_positive",
                evidence={"source": "/v2/suspensions/", "checked_through": "2026-09-25"}),
        path=path)
    assert ledger.read_outcomes(path)[0]["evidence"]["checked_through"] == "2026-09-25"


@pytest.mark.parametrize("broken, why", [
    (lesson(conditions="   "), "kondisi kosong"),
    (lesson(hypothesis=""), "dugaan sebab kosong"),
    (lesson(axis_implicated="likuiditas"), "sumbu yang tidak ada"),
    (lesson(written_on="2026-13-01"), "tanggal mustahil"),
])
def test_lesson_rows_that_must_be_refused(tmp_path, broken, why):
    with pytest.raises(ledger.SchemaError):
        ledger.append_lesson(broken, path=log(tmp_path, "lessons.jsonl"))


def test_a_lesson_may_implicate_no_single_axis(tmp_path):
    """`axis_implicated: null` — the lesson is about the combination, not one axis."""
    path = log(tmp_path, "lessons.jsonl")
    ledger.append_lesson(lesson(axis_implicated=None), path=path)
    assert ledger.read_lessons(path)[0]["axis_implicated"] is None


def test_a_supporting_axis_may_be_implicated(tmp_path):
    ledger.append_lesson(lesson(axis_implicated="history"),
                         path=log(tmp_path, "lessons.jsonl"))


def test_a_file_without_a_schema_is_not_written(tmp_path):
    with pytest.raises(ledger.SchemaError):
        ledger._append_line(log(tmp_path, "catatan.jsonl"), warning())


def test_a_hand_edited_line_fails_loudly(tmp_path):
    """The only way a bad line gets in is by hand, and reading it must not be quiet."""
    path = log(tmp_path, "warnings.jsonl")
    ledger.append_warning(warning(), path=path)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write('{"id": "w-20260912-NICK"}\n')
    with pytest.raises(ledger.SchemaError, match="baris 2"):
        ledger.read_warnings(path)


# --- the row a profile produces ---------------------------------------------
def test_a_warning_carries_the_bar_that_applied_at_the_time():
    """Value, bar and threshold version travel together, or the row cannot be re-judged."""
    built = profile_mod.build("LIFE")
    row = ledger.warning_row(built, credits_spent=0, when="2026-09-11")
    ledger.validate(row, ledger.WARNING_SCHEMA, "warnings.jsonl")

    assert row["id"] == "w-20260911-LIFE"
    assert row["thresholds_version"] == built.thresholds_version
    assert row["axes_fired"] == built.axes_fired
    for axis in profile_mod.AXES:
        assert "threshold" in row["axes"][axis]
    # The supporting axis is carried and flagged, never counted.
    assert row["axes"]["history"]["counted"] is False


def test_the_predicted_horizon_matches_the_backtest():
    """One horizon, two modules. A silent divergence would make the label wrong."""
    assert ledger.PREDICTION_HORIZON_SESSIONS == backtest.HORIZON_SESSIONS
    assert str(backtest.HORIZON_SESSIONS) in ledger.PREDICTION


# --- status is derived, never edited ----------------------------------------
def test_status_comes_from_the_outcome_log_not_from_the_warning_row(tmp_path):
    warnings_path = log(tmp_path, "warnings.jsonl")
    outcomes_path = log(tmp_path, "outcomes.jsonl")
    ledger.append_warning(warning(), path=warnings_path)
    ledger.append_warning(warning(id="w-20260912-NICK", symbol="NICK",
                                  date="2026-09-12"), path=warnings_path)

    assert len(ledger.open_warnings(warnings_path=warnings_path,
                                    outcomes_path=outcomes_path)) == 2

    # An interim note does not close anything.
    ledger.append_outcome(
        outcome(outcome="still_open", days_elapsed=2,
                evidence={"source": "/v2/suspensions/", "checked_through": "2026-09-13"}),
        path=outcomes_path)
    assert len(ledger.open_warnings(warnings_path=warnings_path,
                                    outcomes_path=outcomes_path)) == 2

    ledger.append_outcome(outcome(), path=outcomes_path)
    still = ledger.open_warnings(warnings_path=warnings_path,
                                 outcomes_path=outcomes_path)
    assert [w["id"] for w in still] == ["w-20260912-NICK"]

    # The warning row itself never changed, and the log kept both resolutions.
    assert ledger.read_warnings(warnings_path)[0]["status"] == "open"
    assert len(ledger.read_outcomes(outcomes_path)) == 2
    assert ledger.resolution("w-20260911-ASLI",
                             path=outcomes_path)["outcome"] == "true_positive"


# --- thresholds -------------------------------------------------------------
def test_a_change_appends_history_and_bumps_the_version(thresholds_path):
    doc = ledger.record_change({"concentration": 0.45},
                               reason="6 false positive berturut di bawah 0,45",
                               on="2026-09-21", source="evolve", n_resolved=23,
                               holdout_before=0.31, holdout_after=0.38,
                               evidence=["w-20260911-ASLI"], path=thresholds_path)
    assert doc["version"] == 2
    assert doc["current"]["concentration"] == 0.45
    assert len(doc["history"]) == 2
    entry = doc["history"][-1]
    assert (entry["from"], entry["to"]) == (0.40, 0.45)
    assert entry["n_resolved"] == 23
    # And it survived the round trip through the file.
    assert ledger.load_thresholds(thresholds_path)["current"]["concentration"] == 0.45


@pytest.mark.parametrize("missing", ["n_resolved", "holdout_before",
                                     "holdout_after", "evidence"])
def test_an_automatic_change_must_cite_its_evidence(thresholds_path, missing):
    """A bar the evolve step cannot justify is overfitting with a changelog."""
    kwargs = {"n_resolved": 23, "holdout_before": 0.31, "holdout_after": 0.38,
              "evidence": ["w-20260911-ASLI"]}
    kwargs.pop(missing)
    if missing == "evidence":
        kwargs["evidence"] = []
    with pytest.raises(ledger.ThresholdsInvalid):
        ledger.record_change({"concentration": 0.45}, reason="karena",
                             on="2026-09-21", source="evolve",
                             path=thresholds_path, **kwargs)


def test_a_change_is_clamped_into_its_own_bounds(thresholds_path):
    """The floor and ceiling are a human's fence. The file never stores a bar outside it."""
    doc = ledger.record_change({"concentration": 0.95}, reason="uji pagar",
                               on="2026-09-21", source="bootstrap",
                               path=thresholds_path)
    assert doc["current"]["concentration"] == 0.75
    assert doc["history"][-1]["to"] == 0.75


def test_a_change_without_a_reason_is_refused(thresholds_path):
    with pytest.raises(ledger.ThresholdsInvalid):
        ledger.record_change({"concentration": 0.5}, reason="   ",
                             source="bootstrap", path=thresholds_path)


def test_every_recorded_version_can_be_rebuilt(thresholds_path):
    """Three changes, then every version in the history reconstructed from the file."""
    ledger.record_change({"concentration": 0.45}, reason="langkah satu",
                         on="2026-09-12", source="bootstrap", path=thresholds_path)
    ledger.record_change({"volume_anomaly": 6.0}, reason="langkah dua",
                         on="2026-09-13", source="bootstrap", path=thresholds_path)
    ledger.record_change({"concentration": 0.50}, reason="langkah tiga",
                         on="2026-09-14", source="bootstrap", path=thresholds_path)

    doc = ledger.load_thresholds(thresholds_path)
    assert ledger.reachable_versions(doc) == [0, 1, 2, 3, 4]

    expected = {
        4: {"concentration": 0.50, "volume_anomaly": 6.0},
        3: {"concentration": 0.45, "volume_anomaly": 6.0},
        2: {"concentration": 0.45, "volume_anomaly": 5.0},
        1: {"concentration": 0.40, "volume_anomaly": 5.0},
        0: {"volume_anomaly": 5.0},        # concentration had no bar yet
    }
    for version, current in expected.items():
        rebuilt = ledger.reconstruct(doc, version)
        assert rebuilt["current"] == current, f"versi {version} tidak cocok"
        assert rebuilt["version"] == version
        ledger.validate_thresholds(rebuilt)


def test_a_version_outside_the_history_is_refused(thresholds_path):
    doc = ledger.load_thresholds(thresholds_path)
    with pytest.raises(ledger.ThresholdsInvalid):
        ledger.reconstruct(doc, 99)
    with pytest.raises(ledger.ThresholdsInvalid):
        ledger.reconstruct(doc, -5)


def test_rollback_restores_the_values_and_keeps_the_record(thresholds_path):
    """The bars go back; the version number and the history go forward.

    A rollback that rewound the version would erase the evidence of the change it
    undid — and then nothing in the file would show it ever happened.
    """
    ledger.record_change({"concentration": 0.45}, reason="naikkan",
                         on="2026-09-12", source="bootstrap", path=thresholds_path)
    ledger.record_change({"concentration": 0.60}, reason="naikkan lagi",
                         on="2026-09-13", source="bootstrap", path=thresholds_path)

    doc = ledger.rollback(1, reason="dua langkah terakhir mengejar derau",
                          on="2026-09-14", path=thresholds_path)

    assert doc["current"]["concentration"] == 0.40      # the version-1 value
    assert doc["version"] == 4                          # forward, not back
    assert len(doc["history"]) == 4                     # nothing was dropped
    assert doc["history"][-1]["source"] == "rollback"
    assert doc["history"][-1]["from"] == 0.60

    # And the rollback is itself reversible: version 3 is still reconstructible.
    assert ledger.reconstruct(doc, 3)["current"]["concentration"] == 0.60


def test_rollback_refuses_to_drop_an_axis_silently(tmp_path):
    """Rolling back past an axis' introduction would remove a bar with no record."""
    path = str(tmp_path / "thresholds.json")
    doc = thresholds_doc(
        version=2, updated_on="2026-09-02",
        current={"concentration": 0.40, "volume_anomaly": 5.0, "catalyst": 0.10},
        history=thresholds_doc()["history"] + [
            {"version": 2, "on": "2026-09-02", "axis": "catalyst", "from": None,
             "to": 0.10, "reason": "sumbu katalis masuk profil", "source": "bootstrap"}])
    doc["bounds"]["catalyst"] = {"floor": 0.0, "ceiling": 0.5}
    open(path, "w", encoding="utf-8").write(json.dumps(doc))

    with pytest.raises(ledger.ThresholdsInvalid, match="catalyst"):
        ledger.rollback(1, reason="coba hapus diam-diam", path=path)


def test_a_document_whose_bar_sits_outside_its_bounds_is_refused(tmp_path):
    path = str(tmp_path / "thresholds.json")
    doc = thresholds_doc(current={"concentration": 0.90, "volume_anomaly": 5.0})
    open(path, "w", encoding="utf-8").write(json.dumps(doc))
    with pytest.raises(ledger.ThresholdsInvalid, match="langit"):
        ledger.load_thresholds(path)


def test_a_history_entry_newer_than_the_document_is_refused(tmp_path):
    path = str(tmp_path / "thresholds.json")
    doc = thresholds_doc()
    doc["history"][0]["version"] = 9
    open(path, "w", encoding="utf-8").write(json.dumps(doc))
    with pytest.raises(ledger.ThresholdsInvalid):
        ledger.load_thresholds(path)


def test_a_missing_thresholds_file_raises_rather_than_defaults(tmp_path):
    """No fallback constant. A bar nobody chose is worse than no answer."""
    with pytest.raises(ledger.ThresholdsInvalid):
        ledger.load_thresholds(str(tmp_path / "tidak-ada.json"))


# --- the files as they are shipped ------------------------------------------
def test_the_shipped_thresholds_validate_and_replay():
    """The document in `state/` is the one the axes read. It must pass its own schema."""
    doc = ledger.load_thresholds()
    versions = ledger.reachable_versions(doc)
    assert versions, "riwayat kosong — tidak ada versi yang bisa dikembalikan"
    for version in versions:
        ledger.validate_thresholds(ledger.reconstruct(doc, version))


def test_the_three_logs_exist_and_parse():
    """Mirrors the command in the task's completion criteria, for all three logs.

        python3 -c "import json;[json.loads(l) for l in open('state/warnings.jsonl')]"
    """
    for path in ledger.APPEND_ONLY_PATHS:
        assert os.path.exists(path), f"{path} tidak ada"
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    json.loads(line)
    ledger.read_warnings()
    ledger.read_outcomes()
    ledger.read_lessons()


def test_ensure_files_never_truncates(tmp_path):
    ledger.ensure_files(str(tmp_path))
    path = log(tmp_path, "warnings.jsonl")
    ledger.append_warning(warning(), path=path)
    ledger.ensure_files(str(tmp_path))
    assert len(ledger.read_warnings(path)) == 1


# --- nothing here is a verdict ----------------------------------------------
def test_the_vocabulary_names_no_verdict():
    """The state files describe. `riset/red-team.md` §D11 rules out the rest."""
    banned = ("beli", "jual", "buy", "sell", "aman", "bahaya", "merah", "hijau",
              "rekomendasi", "target")
    words = " ".join(ledger.OUTCOMES + ledger.WARNING_STATUSES
                     + ledger.PREDICTIONS + ledger.CHANGE_SOURCES).lower()
    for word in banned:
        assert word not in words


def test_summary_reports_the_four_files():
    text = ledger.summary()
    for line in ("peringatan", "hasil", "pelajaran", "ambang"):
        assert line in text


# --- guards on the fixtures themselves --------------------------------------
def test_the_fixtures_are_valid_to_begin_with(tmp_path):
    """Otherwise every rejection test above would pass for the wrong reason."""
    ledger.append_warning(warning(), path=log(tmp_path, "warnings.jsonl"))
    ledger.append_outcome(outcome(), path=log(tmp_path, "outcomes.jsonl"))
    ledger.append_lesson(lesson(), path=log(tmp_path, "lessons.jsonl"))
    assert not math.isnan(warning()["axes_fired"])
    assert date.fromisoformat(warning()["date"]) == date(2026, 9, 11)
