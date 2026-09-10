"""The four state files, and the only writer allowed to touch them.

`riset/spec.md` §4 opens with the reason this module exists: *"Ini yang akan
dibuka juri. Bentuknya penting."* The technical-depth criterion is scored against
the GitHub repository, so a claim about self-correction that has no file behind it
is worth nothing. These four files are the file behind it:

    state/warnings.jsonl    what the system said, when, and against which bars
    state/outcomes.jsonl    what actually happened, with the announcement's PDF
    state/lessons.jsonl     what was learned from the gap between the two
    state/thresholds.json   the bars themselves, carrying their own change history

## Append-only is a property of the writer, not a convention

The first three are append-only. Not "we try not to rewrite them" — this module
has exactly one function that writes a line (`_append_line`), it opens with mode
`"a"`, and `app/tests/test_ledger.py` walks this file's syntax tree to prove no
other call site opens a log any other way. The reason is evidential rather than
technical: a warning that can be edited after the fact proves nothing about
prediction. The row written on 11 September has to still be the row written on 11
September when a judge reads it on 30 September.

That has one consequence worth stating plainly. `status` in a warning row is the
status **at the moment it was written**, and it stays `"open"` forever. The current
state of a warning is *derived* — `resolution()` reads `outcomes.jsonl` and returns
the latest resolution for that id. Nothing is ever mutated in place.

## Schema validation happens at write time

*"Baris rusak lebih buruk daripada tidak ada baris."* A malformed row is worse than
a missing one because it is discovered late, usually by the reader it was written
for. So every row goes through `validate()` before it reaches the file, and the
validator refuses `NaN` and `Infinity` too: `json.dumps` emits both happily and
neither is JSON, which would break the one command a judge is most likely to run —

    python3 -c "import json;[json.loads(l) for l in open('state/warnings.jsonl')]"

Reads validate as well. A row can only be malformed if it was hand-edited, and a
hand-edited state file should fail loudly rather than be quietly tolerated.

## thresholds.json carries its own history

`state/thresholds.json` is the one file that is rewritten, because it is a document
and not a log. What makes that safe is that every change is recorded *inside it*:
`history` holds one entry per axis moved, with the value it moved from, the reason,
the number of resolved warnings behind the decision, and the hold-out numbers before
and after. `reconstruct()` replays that history backwards, so the document as it
stood at any recorded version can be rebuilt from the file alone — no git
archaeology, no separate backup. `rollback()` then writes that reconstruction
forward as a new version, which means a rollback is itself a recorded, reversible
change.

An entry produced by the evolve step (task 17) must cite its evidence: `n_resolved`,
`holdout_before`, `holdout_after` and at least one `evidence` row are required when
`source == "evolve"`. A bootstrap entry — a human choosing a starting bar, with no
resolved warnings to point at yet — is not asked for numbers it cannot have.

Zero credits: nothing here opens a socket.
"""
import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config, profile as profile_mod  # noqa: E402

# --- paths ------------------------------------------------------------------
WARNINGS_PATH = os.path.join(config.STATE_DIR, "warnings.jsonl")
OUTCOMES_PATH = os.path.join(config.STATE_DIR, "outcomes.jsonl")
LESSONS_PATH = os.path.join(config.STATE_DIR, "lessons.jsonl")
THRESHOLDS_PATH = os.path.join(config.STATE_DIR, "thresholds.json")

# The three append-only logs, in the order a reader should meet them.
APPEND_ONLY_PATHS = (WARNINGS_PATH, OUTCOMES_PATH, LESSONS_PATH)


# --- vocabulary -------------------------------------------------------------
# The horizon the product predicts against. Mirrors `app.backtest.HORIZON_SESSIONS`
# rather than importing it, to keep this module's import graph small; the test
# asserts the two numbers agree, so they cannot drift apart silently.
PREDICTION_HORIZON_SESSIONS = 10
PREDICTION = (f"cooling_down_suspension_within_"
              f"{PREDICTION_HORIZON_SESSIONS}_trading_days")
PREDICTIONS = (PREDICTION,)

# A warning is written open and stays open in its own line forever; `resolved`
# exists for a row written after the fact (a backfill), never for an edit.
WARNING_STATUSES = ("open", "resolved")

# `riset/spec.md` §4: outcome is one of four.
OUTCOMES = ("true_positive", "false_positive", "still_open", "expired")
# `still_open` is an interim note — the horizon has not run out yet — so it does
# not close a warning. The other three do.
TERMINAL_OUTCOMES = ("true_positive", "false_positive", "expired")

# Where a threshold change came from. `evolve` is the only one asked to cite.
CHANGE_SOURCES = ("bootstrap", "evolve", "rollback")

WARNING_ID_RE = re.compile(r"^w-\d{8}-[A-Z0-9]{2,10}$")

NUMBER = (int, float)


class SchemaError(ValueError):
    """A row does not match its schema, and was therefore not written.

    Carries the field that failed, because "invalid row" without a field name
    sends the reader back to the schema instead of to the bug.
    """


class ThresholdsInvalid(ValueError):
    """`state/thresholds.json` cannot be read, validated, or replayed."""


# --- a very small validator -------------------------------------------------
# Standard library only (the whole product is), so no jsonschema. The schemas
# below are the specification; this is the thirty lines that enforce them.
@dataclass(frozen=True)
class Field:
    """One key's contract: its type, whether it may be absent or null, and a check."""

    kind: tuple
    required: bool = True
    nullable: bool = False
    check: object = None          # value -> error message, or None when fine


def _type_name(kind):
    return " atau ".join(k.__name__ for k in kind)


def _typed(value, kind):
    """`isinstance` with booleans excluded from the numeric types.

    `True` is an `int` in Python. A `fired` flag landing in a `credits_spent`
    field would otherwise validate, and the row would read as one credit.
    """
    if isinstance(value, bool) and bool not in kind:
        return False
    return isinstance(value, kind)


def validate(row, schema, where):
    """Raise `SchemaError` unless `row` matches `schema`. Returns the row.

    Unknown keys are allowed — a later task may carry more context on a row and an
    old reader should not reject it — but every declared key is enforced.
    """
    if not isinstance(row, dict):
        raise SchemaError(f"{where}: baris harus berupa objek JSON, "
                          f"bukan {type(row).__name__}.")
    for name, field in schema.items():
        if name not in row:
            if field.required:
                raise SchemaError(f"{where}: field wajib {name!r} tidak ada.")
            continue
        value = row[name]
        if value is None:
            if field.nullable:
                continue
            raise SchemaError(f"{where}: field {name!r} tidak boleh null.")
        if not _typed(value, field.kind):
            raise SchemaError(
                f"{where}: field {name!r} harus bertipe {_type_name(field.kind)}, "
                f"bukan {type(value).__name__}.")
        if field.check is not None:
            problem = field.check(value)
            if problem:
                raise SchemaError(f"{where}: field {name!r} {problem}")
    _dumps(row, where)
    return row


def _dumps(row, where):
    """Serialise, refusing NaN/Infinity — `json.dumps` writes both, neither is JSON."""
    try:
        return json.dumps(row, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise SchemaError(
            f"{where}: baris tidak bisa diserialkan sebagai JSON: {exc}") from None


# --- reusable checks --------------------------------------------------------
def _is_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return "harus bertanggal YYYY-MM-DD."
    return None


def _nonempty(value):
    return "tidak boleh kosong." if not value.strip() else None


def _one_of(allowed):
    def check(value):
        if value not in allowed:
            return f"harus salah satu dari {', '.join(map(str, allowed))}; dapat {value!r}."
        return None
    return check


def _at_least(minimum):
    def check(value):
        if value < minimum:
            return f"tidak boleh kurang dari {minimum}; dapat {value}."
        return None
    return check


def _matches(pattern, shape):
    def check(value):
        if not pattern.match(value):
            return f"harus berbentuk {shape}; dapat {value!r}."
        return None
    return check


# --- warnings.jsonl ---------------------------------------------------------
def _check_axes(value):
    """The per-axis block: every counted axis present, each with value/bar/fired.

    The three required keys are the three §4 names: what was measured, the bar it
    was measured against, and whether it fired. An axis that could not be measured
    carries `fired: null` — never `false`, which would read as a quiet stock.
    """
    missing = [axis for axis in profile_mod.AXES if axis not in value]
    if missing:
        return f"tidak memuat sumbu {', '.join(missing)}."
    for axis, block in value.items():
        if not isinstance(block, dict):
            return f"sumbu {axis!r} harus berupa objek, bukan {type(block).__name__}."
        for key in ("value", "threshold", "fired"):
            if key not in block:
                return f"sumbu {axis!r} tidak memuat {key!r}."
        if block["fired"] is not None and not isinstance(block["fired"], bool):
            return f"sumbu {axis!r}: 'fired' harus true, false, atau null."
        if block["threshold"] is not None and not _typed(block["threshold"], NUMBER):
            return f"sumbu {axis!r}: 'threshold' harus angka atau null."
        if block["value"] is not None and not isinstance(block["value"], (bool, int, float)):
            return f"sumbu {axis!r}: 'value' harus angka, boolean, atau null."
    return None


WARNING_SCHEMA = {
    "id": Field((str,), check=_matches(WARNING_ID_RE, "w-YYYYMMDD-SIMBOL")),
    "symbol": Field((str,), check=_nonempty),
    "date": Field((str,), check=_is_date),
    "axes": Field((dict,), check=_check_axes),
    "axes_fired": Field((int,), check=_at_least(0)),
    "axes_total": Field((int,), check=_at_least(1)),
    "thresholds_version": Field((int,), check=_at_least(0)),
    "prediction": Field((str,), check=_one_of(PREDICTIONS)),
    "credits_spent": Field((int,), check=_at_least(0)),
    "status": Field((str,), check=_one_of(WARNING_STATUSES)),
}


# --- outcomes.jsonl ---------------------------------------------------------
def _check_evidence(value):
    """Evidence must at minimum name where it was read. The rest depends on outcome."""
    if not str(value.get("source") or "").strip():
        return "wajib menyebut 'source' — endpoint tempat bukti dibaca."
    return None


def _outcome_evidence_problem(outcome, evidence):
    """The outcome-dependent half of the evidence contract.

    A positive must name the announcement — its date, its class, and its `pdf_url` —
    because *"Bukti selalu membawa `pdf_url` kalau ada — itu yang bisa diklik juri"*
    (§4). The key is required even when the announcement carries no link: an explicit
    empty string says "checked, none published", while a missing key says nothing.

    A negative is evidence too, and its evidence is the search that came up empty.
    `checked_through` is the date the horizon was actually read up to. Without it a
    `false_positive` is an assertion rather than a finding.
    """
    if outcome == "true_positive":
        for key in ("suspension_date", "reason_class", "pdf_url"):
            if key not in evidence:
                return (f"bukti untuk true_positive wajib memuat {key!r} "
                        f'(isi "" bila pengumuman tidak memuat tautan).')
        problem = _is_date(evidence["suspension_date"])
        if problem:
            return f"bukti 'suspension_date' {problem}"
    else:
        if "checked_through" not in evidence:
            return ("bukti untuk outcome non-positif wajib memuat 'checked_through' — "
                    "tanggal terakhir yang benar-benar dibaca.")
        problem = _is_date(evidence["checked_through"])
        if problem:
            return f"bukti 'checked_through' {problem}"
    return None


OUTCOME_SCHEMA = {
    "warning_id": Field((str,), check=_matches(WARNING_ID_RE, "w-YYYYMMDD-SIMBOL")),
    "resolved_on": Field((str,), check=_is_date),
    "outcome": Field((str,), check=_one_of(OUTCOMES)),
    "days_elapsed": Field((int,), check=_at_least(0)),
    "evidence": Field((dict,), check=_check_evidence),
}


# --- lessons.jsonl ----------------------------------------------------------
def _check_axis_name(value):
    known = profile_mod.AXES + profile_mod.SUPPORTING_AXES
    if value not in known:
        return f"harus salah satu sumbu {', '.join(known)}; dapat {value!r}."
    return None


LESSON_SCHEMA = {
    "warning_id": Field((str,), check=_matches(WARNING_ID_RE, "w-YYYYMMDD-SIMBOL")),
    "written_on": Field((str,), check=_is_date),
    "conditions": Field((str,), check=_nonempty),
    "expected": Field((str,), check=_nonempty),
    "actual": Field((str,), check=_nonempty),
    "hypothesis": Field((str,), check=_nonempty),
    # Nullable: a lesson may be about the combination rather than about one axis.
    "axis_implicated": Field((str,), nullable=True, check=_check_axis_name),
    "subsector": Field((str,)),
}


# Keyed by filename, not by full path, so an injected temp path validates against
# exactly the same schema the real file does.
SCHEMAS = {
    "warnings.jsonl": WARNING_SCHEMA,
    "outcomes.jsonl": OUTCOME_SCHEMA,
    "lessons.jsonl": LESSON_SCHEMA,
}


def _schema_for(path):
    name = os.path.basename(path)
    if name not in SCHEMAS:
        raise SchemaError(
            f"{name}: bukan salah satu dari tiga log append-only "
            f"({', '.join(SCHEMAS)}). Berkas tanpa skema tidak ditulis.")
    return name, SCHEMAS[name]


# --- the one writer ---------------------------------------------------------
def _append_line(path, row):
    """Validate, then append exactly one line. The only writer of a log here.

    Mode `"a"` is the whole point, and the test asserts syntactically that no other
    call in this module opens a log any other way.
    """
    name, schema = _schema_for(path)
    validate(row, schema, name)
    line = _dumps(row, name)
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return row


def append_warning(row, path=None):
    """Append one warning. `path` is injectable so tests never touch real state."""
    return _append_line(path or WARNINGS_PATH, row)


def append_outcome(row, path=None):
    """Append one resolution. What counts as evidence depends on the outcome."""
    validate(row, OUTCOME_SCHEMA, "outcomes.jsonl")
    problem = _outcome_evidence_problem(row["outcome"], row["evidence"])
    if problem:
        raise SchemaError(f"outcomes.jsonl: field 'evidence' {problem}")
    return _append_line(path or OUTCOMES_PATH, row)


def append_lesson(row, path=None):
    """Append one lesson."""
    return _append_line(path or LESSONS_PATH, row)


# --- builders ---------------------------------------------------------------
def warning_id(symbol, when):
    """`w-20260911-ASLI` — the id shape §4 uses. Date first so ids sort by day."""
    day = when if isinstance(when, str) else when.isoformat()
    ticker = str(symbol).upper().replace(".JK", "")
    return f"w-{day.replace('-', '')}-{ticker}"


def warning_row(profile, credits_spent=0, prediction=PREDICTION, when=None,
                status="open"):
    """A `Profile` (task 09) turned into a warning row, bars and version included.

    Built here rather than at the call site so that every warning ever written
    carries the same fields: the value of each axis, **the bar that applied at that
    moment**, and the version of the threshold document those bars came from. A row
    that records the value but not the bar cannot be re-judged after the bars move,
    which is exactly what tasks 15-17 do to it.
    """
    day = when or profile.as_of or date.today().isoformat()
    axes_block = {}
    for reading in profile.readings + profile.supporting:
        axes_block[reading.axis] = {
            "value": reading.value,
            "threshold": reading.threshold,
            "fired": reading.fired,
            "counted": reading.counted,
            "state": reading.state,
        }
    return {
        "id": warning_id(profile.symbol, day),
        "symbol": profile.symbol,
        "date": day,
        "axes": axes_block,
        "axes_fired": profile.axes_fired,
        "axes_total": profile.axes_total,
        "thresholds_version": profile.thresholds_version,
        "prediction": prediction,
        "credits_spent": int(credits_spent),
        "status": status,
    }


# --- readers ----------------------------------------------------------------
def _read(path, schema, name):
    """Every row in a log, validated. A hand-edited file fails here, loudly."""
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as fh:
        for number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise SchemaError(f"{name} baris {number}: bukan JSON ({exc}).") from None
            validate(row, schema, f"{name} baris {number}")
            rows.append(row)
    return rows


def read_warnings(path=None):
    return _read(path or WARNINGS_PATH, WARNING_SCHEMA, "warnings.jsonl")


def read_outcomes(path=None):
    return _read(path or OUTCOMES_PATH, OUTCOME_SCHEMA, "outcomes.jsonl")


def read_lessons(path=None):
    return _read(path or LESSONS_PATH, LESSON_SCHEMA, "lessons.jsonl")


def resolution(wid, outcomes=None, path=None):
    """The latest resolution for a warning, or None. Status is derived, never edited.

    "Latest" is the last line written, not the newest `resolved_on`: the log is the
    order things were decided in, and that order is the audit trail.
    """
    rows = outcomes if outcomes is not None else read_outcomes(path)
    found = None
    for row in rows:
        if row["warning_id"] == wid:
            found = row
    return found


def open_warnings(warnings=None, outcomes=None, warnings_path=None,
                  outcomes_path=None):
    """Warnings with no terminal outcome yet — what the adjudicator picks up."""
    rows = warnings if warnings is not None else read_warnings(warnings_path)
    resolved = outcomes if outcomes is not None else read_outcomes(outcomes_path)
    closed = {r["warning_id"] for r in resolved if r["outcome"] in TERMINAL_OUTCOMES}
    return [w for w in rows if w["id"] not in closed]


# --- thresholds.json --------------------------------------------------------
def _entry_date(entry):
    """The date of a change. `on` is what the file uses; `date` is read as an alias."""
    return entry.get("on") or entry.get("date")


def _history_entry_problem(entry):
    if not isinstance(entry, dict):
        return f"harus berupa objek, bukan {type(entry).__name__}."
    for key in ("version", "axis", "from", "to", "reason"):
        if key not in entry:
            return f"tidak memuat {key!r}."
    if not _typed(entry["version"], (int,)):
        return "'version' harus bilangan bulat."
    if _entry_date(entry) is None:
        return "tidak memuat tanggal ('on')."
    problem = _is_date(_entry_date(entry))
    if problem:
        return f"tanggal {problem}"
    for key in ("from", "to"):
        if entry[key] is not None and not _typed(entry[key], NUMBER):
            return f"{key!r} harus angka atau null."
    if not str(entry["reason"] or "").strip():
        return "'reason' tidak boleh kosong — perubahan tanpa alasan tidak bisa ditinjau."
    source = entry.get("source", "bootstrap")
    if source not in CHANGE_SOURCES:
        return f"'source' harus salah satu dari {', '.join(CHANGE_SOURCES)}."
    if source == "evolve":
        # The evolve step (task 17) moves bars automatically. A move it cannot
        # justify with resolved warnings and hold-out numbers is not reviewable,
        # and an unreviewable automatic change is exactly the overfitting that task
        # warns about, wearing a changelog.
        for key in ("n_resolved", "holdout_before", "holdout_after"):
            if key not in entry:
                return f"perubahan dari evolve wajib memuat {key!r}."
        if not _typed(entry["n_resolved"], (int,)) or entry["n_resolved"] < 0:
            return "'n_resolved' harus bilangan bulat >= 0."
        for key in ("holdout_before", "holdout_after"):
            # Not nullable, unlike everywhere else in this file: a hold-out number
            # the evolve step could not compute is the case where it must not move
            # the bar at all, so `null` here would record a decision made blind.
            if not _typed(entry[key], NUMBER):
                return f"{key!r} harus angka — perubahan otomatis tanpa angka hold-out tidak sah."
        evidence = entry.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            return ("perubahan dari evolve wajib memuat 'evidence' — daftar tak kosong "
                    "berisi warning_id atau outcome yang memicunya.")
    return None


def _check_history(value):
    for index, entry in enumerate(value):
        problem = _history_entry_problem(entry)
        if problem:
            return f"entri {index}: {problem}"
    return None


THRESHOLDS_SCHEMA = {
    "version": Field((int,), check=_at_least(0)),
    "updated_on": Field((str,), check=_is_date),
    "current": Field((dict,)),
    "bounds": Field((dict,)),
    "history": Field((list,), check=_check_history),
}


def validate_thresholds(doc):
    """Schema plus the two document-level invariants: bars in bounds, history sane."""
    try:
        validate(doc, THRESHOLDS_SCHEMA, "thresholds.json")
    except SchemaError as exc:
        raise ThresholdsInvalid(str(exc)) from None
    for axis, value in doc["current"].items():
        if not _typed(value, NUMBER):
            raise ThresholdsInvalid(
                f"thresholds.json: current[{axis!r}] harus angka, "
                f"bukan {type(value).__name__}.")
        row = (doc.get("bounds") or {}).get(axis) or {}
        floor, ceiling = row.get("floor"), row.get("ceiling")
        if floor is not None and value < floor:
            raise ThresholdsInvalid(
                f"thresholds.json: current[{axis!r}] = {value} di bawah lantai {floor}.")
        if ceiling is not None and value > ceiling:
            raise ThresholdsInvalid(
                f"thresholds.json: current[{axis!r}] = {value} di atas langit {ceiling}.")
    if any(entry["version"] > doc["version"] for entry in doc["history"]):
        raise ThresholdsInvalid(
            "thresholds.json: riwayat memuat versi lebih baru daripada 'version'.")
    return doc


def load_thresholds(path=None):
    """Read and validate the document. Never falls back to a default."""
    target = path or THRESHOLDS_PATH
    try:
        with open(target, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ThresholdsInvalid(f"Ambang tidak terbaca di {target}: {exc}") from None
    return validate_thresholds(doc)


def _groups(doc):
    """History grouped by the version each entry produced."""
    out = {}
    for entry in doc["history"]:
        out.setdefault(entry["version"], []).append(entry)
    return out


def reachable_versions(doc):
    """Every version this document can be rebuilt as, oldest first.

    Walk down from the current version while each next version down has a change
    group. A gap stops the walk: below it the file no longer knows what the bars
    were, and inventing them would be worse than refusing.
    """
    groups = _groups(doc)
    current = doc["version"]
    versions = [current]
    while current in groups:
        current -= 1
        versions.append(current)
    return sorted(versions)


def reconstruct(doc, version):
    """The document as it stood at `version`, replayed from its own history.

    This is the property the file format exists for: a rollback needs nothing but
    the file. Every change from the current version down to `version + 1` is
    reversed, each axis restored to that entry's `from` — and removed entirely when
    `from` is null, because that is what "this axis had no bar yet" means.
    """
    available = reachable_versions(doc)
    if version not in available:
        raise ThresholdsInvalid(
            f"thresholds.json: versi {version} tidak bisa direkonstruksi; "
            f"yang tersedia di riwayat: {', '.join(str(v) for v in available)}.")
    groups = _groups(doc)
    out = json.loads(json.dumps(doc))          # deep copy, no shared sub-objects
    for step in range(doc["version"], version, -1):
        for entry in reversed(groups[step]):
            axis, previous = entry["axis"], entry["from"]
            if previous is None:
                out["current"].pop(axis, None)
            else:
                out["current"][axis] = previous
    out["version"] = version
    remaining = [e for e in out["history"] if e["version"] <= version]
    out["history"] = remaining
    out["updated_on"] = (_entry_date(remaining[-1]) if remaining
                         else doc.get("updated_on"))
    return out


def _atomic_write_json(path, doc):
    """Write a document by replacing it, so a crash cannot leave half a file.

    The only truncating write in this module, and it never touches a log.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    temporary = f"{path}.tmp"
    with open(temporary, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, allow_nan=False, indent=2)
        fh.write("\n")
    os.replace(temporary, path)


def record_change(changes, reason, on=None, source="evolve", n_resolved=None,
                  holdout_before=None, holdout_after=None, evidence=None,
                  path=None):
    """Move one or more bars, appending the history that makes the move reversible.

    `changes` is `{axis: new_value}`. The new values are clamped into `bounds`
    before anything is written — the same clamp `app.axes.threshold()` applies on
    read, applied here too so the file never *stores* a bar outside the fence a
    human set.

    History entries are appended, never rewritten: an older version's entry is what
    `reconstruct()` replays, so losing one loses a rollback target.
    """
    target = path or THRESHOLDS_PATH
    doc = load_thresholds(target)
    if not changes:
        raise ThresholdsInvalid("thresholds.json: tidak ada perubahan yang diminta.")
    day = on or date.today().isoformat()
    version = doc["version"] + 1
    entries = []
    for axis, value in changes.items():
        row = (doc.get("bounds") or {}).get(axis) or {}
        floor, ceiling = row.get("floor"), row.get("ceiling")
        moved = float(value)
        if floor is not None:
            moved = max(moved, float(floor))
        if ceiling is not None:
            moved = min(moved, float(ceiling))
        entry = {"version": version, "on": day, "axis": axis,
                 "from": doc["current"].get(axis), "to": moved,
                 "reason": reason, "source": source}
        if source == "evolve":
            entry.update({"n_resolved": n_resolved,
                          "holdout_before": holdout_before,
                          "holdout_after": holdout_after,
                          "evidence": list(evidence or [])})
        problem = _history_entry_problem(entry)
        if problem:
            raise ThresholdsInvalid(f"thresholds.json: perubahan ditolak — {problem}")
        doc["current"][axis] = moved
        entries.append(entry)
    doc["version"] = version
    doc["updated_on"] = day
    doc["history"] = list(doc["history"]) + entries
    validate_thresholds(doc)
    _atomic_write_json(target, doc)
    return doc


def rollback(version, reason, on=None, path=None):
    """Restore the bars of an earlier version — as a new, forward version.

    A rollback that rewound `version` and truncated `history` would erase the record
    of the change it is undoing, and the next reader would have no way to see that it
    happened. So the bars go back and the version number goes **forward**, with one
    history entry per axis restored. Rolling back a rollback is therefore just
    another rollback.
    """
    target = path or THRESHOLDS_PATH
    doc = load_thresholds(target)
    previous = reconstruct(doc, version)
    restored = dict(previous["current"])
    # An axis that exists now but did not exist then cannot be expressed as a value,
    # and dropping it silently would change the profile with no record of it.
    vanished = [axis for axis in doc["current"] if axis not in restored]
    if vanished:
        raise ThresholdsInvalid(
            f"thresholds.json: rollback ke versi {version} akan menghilangkan sumbu "
            f"{', '.join(vanished)}. Hapus sumbunya lewat perubahan tersendiri, "
            f"bukan diam-diam lewat rollback.")
    changes = {axis: value for axis, value in restored.items()
               if doc["current"].get(axis) != value}
    if not changes:
        return doc
    return record_change(changes, reason=f"rollback ke versi {version}: {reason}",
                         on=on, source="rollback", path=target)


# --- files ------------------------------------------------------------------
def ensure_files(state_dir=None):
    """Create the three logs if they are absent. Never truncates an existing one."""
    directory = state_dir or config.STATE_DIR
    os.makedirs(directory, exist_ok=True)
    paths = tuple(os.path.join(directory, os.path.basename(p))
                  for p in APPEND_ONLY_PATHS)
    for path in paths:
        if not os.path.exists(path):
            with open(path, "a", encoding="utf-8"):
                pass
    return paths


# --- summary ----------------------------------------------------------------
def summary(warnings_path=None, outcomes_path=None, lessons_path=None,
            thresholds_path=None):
    """What the four files currently hold, in Indonesian. Reads nothing else."""
    warnings = read_warnings(warnings_path)
    outcomes = read_outcomes(outcomes_path)
    lessons = read_lessons(lessons_path)
    doc = load_thresholds(thresholds_path)
    still_open = open_warnings(warnings, outcomes)
    kinds = {name: sum(1 for o in outcomes if o["outcome"] == name)
             for name in OUTCOMES}
    return "\n".join([
        f"peringatan : {len(warnings)} baris, {len(still_open)} masih terbuka",
        "hasil      : " + f"{len(outcomes)} baris ("
        + ", ".join(f"{name} {count}" for name, count in kinds.items()) + ")",
        f"pelajaran  : {len(lessons)} baris",
        f"ambang     : versi {doc['version']} per {doc['updated_on']}, "
        f"{len(doc['history'])} perubahan tercatat; bisa dikembalikan ke versi "
        + ", ".join(str(v) for v in reachable_versions(doc)),
    ])


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Empat berkas state: buat yang belum ada, lalu ringkas isinya.")
    ap.add_argument("--ensure", action="store_true",
                    help="buat berkas log yang belum ada (tidak pernah menimpa)")
    args = ap.parse_args(argv)
    if args.ensure:
        for path in ensure_files():
            print(f"ada: {os.path.relpath(path, config.PKG_ROOT)}")
    print(summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
