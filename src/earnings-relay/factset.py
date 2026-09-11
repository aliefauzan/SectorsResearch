#!/usr/bin/env python3
"""
Facts get locked before a sentence is written, and a locked fact cannot move.

A `FactSet` is the frozen set of numbers one draft is allowed to talk about. Every fact
carries where it came from — field, endpoint, period, `as_of` — and a `fact_id` that is a
hash of its own content, so a claim that names a `fact_id` is naming an exact value and
not a slot that might have been refilled since.

    from factset import build_factset, validate, lock, restate

    facts = build_factset("ADRO", "q1-2026", rows, comparator, "recorded", endpoint, as_of)
    ok, reasons = validate(facts)
    locked = lock(facts)                 # locked["facts"][0]["raw_value"] = 1 -> raises

Three properties the rest of the product depends on:

  * **Deterministic.** `source_hash` is a hash of the canonical JSON of the rows, and
    `fact_id` is a hash of the fact's own content. The same inputs and the same
    `rule_version` produce byte-identical ids in a different process (PRD §16), which is
    what makes a run reproducible rather than merely repeatable.
  * **Immutable after lock.** `lock()` returns a frozen mapping whose `__setitem__`
    raises `FactSetLocked`, all the way down through the nested facts. This is a guard,
    not a convention — PRD §15 forbids locking a FactSet before validation finishes, and
    forbids anything touching it afterwards.
  * **Restated, never overwritten.** A new `source_as_of` for the same period produces
    version 2 and a list of the `fact_id`s whose value changed (ER-FR-07). `relay.py`
    pushes every claim citing one of those back to `needs_review` (AT-05).

    python3 factset.py    # determinism, lock, restatement, and every validate() reason
"""
import copy
import hashlib
import json
import time

#: Stamped on every FactSet. Bump when a formula or a validation rule changes, because a
#: figure computed under different rules is not the same figure even if the inputs match.
RULE_VERSION = "er-rules-1"
FORMULA_VERSION = "er-formula-1"

#: The fields a FactSet is built from, and the unit each one is in. A field that is not
#: in this map has an unknown unit and is rejected (ER-FR-05) rather than assumed to be
#: rupiah — the SGX and KLSE surfaces of the same API are not in rupiah at all.
UNITS = {
    "revenue": "IDR",
    "earnings": "IDR",
    "gross_profit": "IDR",
    "operating_pnl": "IDR",
    "total_assets": "IDR",
    "total_equity": "IDR",
    "total_liabilities": "IDR",
    "operating_cash_flow": "IDR",
    "capex": "IDR",
}

#: Without these two the three metrics cannot be computed at all, so a null one is a
#: validation failure rather than an `unknown` metric (PRD §10: missing is unknown, but
#: a required missing field stops the run before a draft exists).
REQUIRED_FIELDS = ("revenue", "earnings")

#: Reason codes this module emits. They reach the UI and the audit log verbatim.
REQUIRED_FIELD_NULL = "required_field_null"
COMPARATOR_KIND_MISMATCH = "comparator_kind_mismatch"
UNKNOWN_UNIT = "unknown_unit"
COMPARATOR_UNAVAILABLE = "comparator_unavailable"
NO_TARGET_PERIOD = "no_target_period"


class FactSetLocked(Exception):
    """An attempt to change a FactSet after `fact_locked`.

    PRD §12 makes `fact_locked` the point after which the numbers are evidence rather
    than working state. Raising here is the difference between a draft that can be
    audited and one that merely looks like it can.
    """


class FactSetInvalid(Exception):
    """A FactSet was locked before it validated. `validate()` runs first, always."""


def canonical_json(obj):
    """Stable JSON: sorted keys, no incidental whitespace.

    `json.dumps` with defaults is not stable across dict insertion order, which would
    make `source_hash` depend on the order a payload happened to be parsed in and break
    the determinism gate silently.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fact_id(symbol, period_key, field, raw_value):
    """A fact's identity is its content. Same number, same id; new number, new id."""
    return _sha(f"{symbol}|{period_key}|{field}|{canonical_json(raw_value)}")[:12]


def _fact(symbol, row, field, endpoint, as_of):
    raw = row.get(field)
    period = row.get("period_key")
    # Divergence 4: the capex slot has two possible vendor names and the evidence drawer
    # must show the one the API actually used, not the canonical one this product picked.
    source_field = (row.get("capex_source_field") if field == "capex" else field)
    return {
        "fact_id": fact_id(symbol, period, field, raw),
        "field": field,
        "source_field": source_field,
        "raw_value": raw,
        # Nothing is rescaled: the payload is already in whole rupiah, so normalization
        # is the float cast and the recorded absence of a value stays absent.
        "normalized_value": None if raw is None else float(raw),
        "unit": UNITS.get(field),
        "period": period,
        "endpoint": endpoint.format(symbol=symbol) if endpoint else None,
        "as_of": as_of,
        # PRD §10: an approximate or inferred value must carry a quality flag. Nothing
        # on disk is inferred, so everything recorded is `reported`.
        "quality": "reported" if raw is not None else "missing",
        "role": None,           # filled in by build_factset: target or comparator
    }


def build_factset(symbol, period_key, rows, comparator, source, endpoint,
                  as_of, version=1, now=None):
    """The facts one draft may talk about, plus the provenance that makes them evidence.

    `rows` is `{period_key: normalized_row}` and must contain `period_key`; the
    comparator period is included when it is present. `comparator` is
    `{"mode","key","status","reason_code"}` as `periods.select_comparator` produced it.
    """
    facts = []
    for role, key in (("target", period_key), ("comparator", comparator.get("key"))):
        row = (rows or {}).get(key)
        if not row:
            continue
        for field in UNITS:
            fact = _fact(symbol, row, field, endpoint, as_of)
            fact["role"] = role
            facts.append(fact)

    source_hash = _sha(canonical_json(rows))
    return {
        "fact_set_id": _sha(f"{symbol}|{period_key}|{source_hash}|{version}")[:12],
        "symbol": symbol,
        "period_key": period_key,
        "comparator": dict(comparator),
        "source": source,
        "endpoint": endpoint,
        "as_of": as_of,
        "version": version,
        "source_hash": source_hash,
        "rule_version": RULE_VERSION,
        "formula_version": FORMULA_VERSION,
        "locked_at": None,
        "facts": facts,
        # Kept so `restate()` can rebuild with exactly the same shape, and so the audit
        # trail can show what the run was actually looking at.
        "rows": copy.deepcopy(rows or {}),
        "built_at": now if now is not None else time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def by_id(factset, wanted):
    """One fact, or None. Nothing indexes `facts` by position."""
    for fact in factset["facts"]:
        if fact["fact_id"] == wanted:
            return fact
    return None


def facts_for(factset, role=None, field=None):
    """The facts matching a role and/or a field, in build order."""
    return [f for f in factset["facts"]
            if (role is None or f["role"] == role)
            and (field is None or f["field"] == field)]


def value_of(factset, role, field):
    """The normalized value of one field in one role, or None if it is not there."""
    matches = facts_for(factset, role, field)
    return matches[0]["normalized_value"] if matches else None


def validate(factset):
    """ER-FR-05. `(ok, [reason_codes])` — and a zero denominator is NOT a rejection.

    A denominator of zero produces an `unknown` metric downstream, which is a result the
    reviewer can act on. A null required field, a comparator of a different kind, or a
    unit this product cannot name are all conditions under which no honest draft exists
    at all, so they stop the run instead.
    """
    reasons = []
    target = facts_for(factset, "target")
    if not target:
        reasons.append(NO_TARGET_PERIOD)

    for fact in target:
        if fact["field"] in REQUIRED_FIELDS and fact["raw_value"] is None:
            reasons.append(REQUIRED_FIELD_NULL)
            break

    for fact in factset["facts"]:
        # The capex slot is legitimately absent on one side of every sector split
        # (divergence 4), and it is not an input to any of the three metrics, so an
        # absent one is not a null failure. Its unit still has to be known.
        if fact["unit"] is None:
            reasons.append(UNKNOWN_UNIT)
            break

    comparator = factset.get("comparator") or {}
    if comparator.get("status") != "ok":
        # Not a rejection: the draft still renders, with the comparison marked unknown
        # and the endpoint that would supply it named on screen.
        reasons.append(comparator.get("reason_code") or COMPARATOR_UNAVAILABLE)
    else:
        target_key = factset.get("period_key") or ""
        comparator_key = comparator.get("key") or ""
        # "Comparator tidak sejenis": a quarter may only be compared with a quarter. Both
        # keys come out of `periods`, so a mismatch here means something built a FactSet
        # by hand with a period key of a different shape.
        if target_key[:1] != "q" or comparator_key[:1] != "q":
            reasons.append(COMPARATOR_KIND_MISMATCH)
        elif not facts_for(factset, "comparator"):
            reasons.append(COMPARATOR_UNAVAILABLE)

    blocking = {REQUIRED_FIELD_NULL, COMPARATOR_KIND_MISMATCH, UNKNOWN_UNIT,
                NO_TARGET_PERIOD}
    ok = not (set(reasons) & blocking)
    return ok, reasons


class _Frozen:
    """A read-only view that raises `FactSetLocked` on any attempt to change it.

    Nested dicts and lists are wrapped too, so `locked["facts"][0]["raw_value"] = 1`
    raises rather than quietly succeeding one level down — which is the mutation that
    would actually matter.
    """

    __slots__ = ("_data",)

    def __init__(self, data):
        object.__setattr__(self, "_data", data)

    def __getitem__(self, key):
        return _freeze(self._data[key])

    def __setitem__(self, key, value):
        raise FactSetLocked(f"{key!r}: this FactSet is locked; restate() it instead")

    def __delitem__(self, key):
        raise FactSetLocked(f"{key!r}: this FactSet is locked")

    def __setattr__(self, name, value):
        raise FactSetLocked(f"{name!r}: this FactSet is locked")

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def __repr__(self):
        return f"Locked({self._data!r})"

    def get(self, key, default=None):
        return _freeze(self._data[key]) if key in self._data else default

    def keys(self):
        return self._data.keys()

    def items(self):
        return ((k, _freeze(v)) for k, v in self._data.items())

    def values(self):
        return (_freeze(v) for v in self._data.values())

    def unfrozen(self):
        """A mutable deep copy. The only sanctioned way back out, and it is a copy."""
        return copy.deepcopy(self._data)

    def append(self, value):
        raise FactSetLocked("this FactSet is locked; nothing can be appended to it")


def _freeze(value):
    if isinstance(value, (dict, list, tuple)):
        return _Frozen(value)
    return value


def lock(factset, now=None):
    """Freeze a validated FactSet. Refuses to lock one that has not validated (PRD §15)."""
    ok, reasons = validate(factset)
    if not ok:
        raise FactSetInvalid(f"{factset['symbol']} {factset['period_key']}: "
                             f"{', '.join(sorted(set(reasons)))}")
    locked = copy.deepcopy(factset)
    locked["locked_at"] = now if now is not None else time.strftime("%Y-%m-%dT%H:%M:%S")
    return _Frozen(locked)


def unlock_copy(locked):
    """A mutable copy of a locked FactSet, for `restate()` and for serialization."""
    return locked.unfrozen() if isinstance(locked, _Frozen) else copy.deepcopy(locked)


def restate(old, new_rows, as_of=None, now=None):
    """ER-FR-07: a new source version makes version 2. It never overwrites version 1.

    Returns `(new_factset, changed_fact_ids)`. `changed_fact_ids` are the OLD ids whose
    value moved, which is what `relay.py` matches claims against — a claim cites the id
    it was written from, and that id is exactly what stopped being true.
    """
    base = unlock_copy(old)
    new = build_factset(base["symbol"], base["period_key"], new_rows,
                        base["comparator"], base["source"], base["endpoint"],
                        as_of if as_of is not None else base["as_of"],
                        version=base["version"] + 1, now=now)

    before = {(f["role"], f["field"]): f for f in base["facts"]}
    after = {(f["role"], f["field"]): f for f in new["facts"]}
    changed = []
    for key, fact in before.items():
        replacement = after.get(key)
        if replacement is None or replacement["fact_id"] != fact["fact_id"]:
            changed.append(fact["fact_id"])
    new["restates"] = base["fact_set_id"]
    new["previous_version"] = base["version"]
    return new, changed


# ------------------------------------------------------------------------------ gates


def _rows(revenue=8004471444300, earnings=2178080414220, prior_revenue=8792499261000,
          prior_earnings=2445263751840):
    def row(period, date, rev, ni):
        return {"symbol": "ADRO", "report_date": date, "period_key": period,
                "quarter_label_seen": None, "capex": 1000, "capex_source_field":
                "capital_expenditure", "source": "recorded", "revenue": rev,
                "earnings": ni, "gross_profit": 1, "operating_pnl": 2,
                "total_assets": 3, "total_equity": 4, "total_liabilities": 5,
                "operating_cash_flow": 6}
    return {"q1-2026": row("q1-2026", "2026-03-31", revenue, earnings),
            "q4-2025": row("q4-2025", "2025-12-31", prior_revenue, prior_earnings)}


def _comparator(status="ok", key="q4-2025", mode="sequential"):
    return {"mode": mode, "key": key, "status": status,
            "reason_code": None if status == "ok" else COMPARATOR_UNAVAILABLE}


def _build(rows=None, comparator=None, **kwargs):
    return build_factset("ADRO", "q1-2026", rows if rows is not None else _rows(),
                         comparator or _comparator(), "recorded",
                         "/v2/financials/quarterly/{symbol}/?n_quarters=4",
                         "2026-09-06", now="2026-09-10T00:00:00", **kwargs)


def check_determinism():
    """Same inputs, same ids — in this process and in any other."""
    failures = []
    first = _build()
    second = _build()
    if first["source_hash"] != second["source_hash"]:
        failures.append("source_hash is not deterministic")
    if [f["fact_id"] for f in first["facts"]] != [f["fact_id"] for f in second["facts"]]:
        failures.append("fact_ids are not deterministic")

    # Shuffled dict insertion order must not move the hash.
    shuffled = {}
    for key in reversed(list(_rows())):
        row = dict(reversed(list(_rows()[key].items())))
        shuffled[key] = row
    if _sha(canonical_json(shuffled)) != first["source_hash"]:
        failures.append("source_hash moved when the dict order changed — canonical_json "
                        "is not sorting keys")

    # A changed number must change exactly that fact's id, and the set hash.
    moved = _build(rows=_rows(revenue=9_000_000_000_000))
    if moved["source_hash"] == first["source_hash"]:
        failures.append("a changed revenue did not move source_hash")
    before = {f["field"]: f["fact_id"] for f in facts_for(first, "target")}
    after = {f["field"]: f["fact_id"] for f in facts_for(moved, "target")}
    differing = {k for k in before if before[k] != after[k]}
    if differing != {"revenue"}:
        failures.append(f"a changed revenue moved {sorted(differing)}, expected revenue")
    if len(first["facts"]) != 2 * len(UNITS):
        failures.append(f"{len(first['facts'])} facts, expected {2 * len(UNITS)}")
    return failures, 6


def check_provenance():
    """Every fact names its endpoint, field, period, unit and as_of. That is the product."""
    failures = []
    built = _build()
    for fact in built["facts"]:
        for key in ("endpoint", "field", "period", "unit", "as_of", "quality"):
            if not fact.get(key):
                failures.append(f"{fact['field']}: no {key}")
        if "{symbol}" in str(fact["endpoint"]):
            failures.append(f"{fact['field']}: the endpoint template was never filled")
        if "ADRO" not in str(fact["endpoint"]):
            failures.append(f"{fact['field']}: the endpoint does not name the symbol")
    if built["rule_version"] != RULE_VERSION or built["formula_version"] != FORMULA_VERSION:
        failures.append("a version stamp is missing")
    capex = facts_for(built, "target", "capex")[0]
    if capex["source_field"] != "capital_expenditure":
        failures.append("the capex fact lost the vendor field name it was read from")
    return failures, len(built["facts"]) + 2


def check_validate():
    """Every reason code, and the one condition that is deliberately NOT a rejection."""
    failures = []
    cases = [
        (_build(), True, None, "a complete FactSet"),
        (_build(rows=_rows(revenue=None)), False, REQUIRED_FIELD_NULL, "null revenue"),
        (_build(rows=_rows(earnings=None)), False, REQUIRED_FIELD_NULL, "null earnings"),
        (_build(rows={}), False, NO_TARGET_PERIOD, "no target period"),
    ]
    for built, expected_ok, reason, why in cases:
        ok, reasons = validate(built)
        if ok != expected_ok:
            failures.append(f"{why}: ok={ok}, expected {expected_ok}")
        if reason and reason not in reasons:
            failures.append(f"{why}: reasons {reasons}, expected {reason}")

    # A zero denominator is a metric-level `unknown`, not a FactSet rejection.
    zero_prior = _build(rows=_rows(prior_revenue=0))
    ok, reasons = validate(zero_prior)
    if not ok:
        failures.append(f"a zero prior revenue rejected the FactSet: {reasons}")

    # An absent comparator is reported but does not reject: the draft still renders.
    absent = _build(rows={"q1-2026": _rows()["q1-2026"]},
                    comparator=_comparator(status="unavailable", key="q1-2025",
                                           mode="yoy"))
    ok, reasons = validate(absent)
    if not ok:
        failures.append("an unavailable comparator rejected the whole FactSet")
    if COMPARATOR_UNAVAILABLE not in reasons:
        failures.append(f"an unavailable comparator was not reported: {reasons}")

    # A comparator of a different kind is a rejection.
    wrong_kind = _build(comparator={"mode": "yoy", "key": "FY2025", "status": "ok",
                                    "reason_code": None})
    ok, reasons = validate(wrong_kind)
    if ok or COMPARATOR_KIND_MISMATCH not in reasons:
        failures.append(f"a non-quarter comparator was accepted: {reasons}")

    # An unknown unit is a rejection.
    unknown_unit = _build()
    unknown_unit["facts"][0]["unit"] = None
    ok, reasons = validate(unknown_unit)
    if ok or UNKNOWN_UNIT not in reasons:
        failures.append(f"an unknown unit was accepted: {reasons}")
    return failures, len(cases) + 4


def check_lock():
    """Locked means locked, one level down as well as at the top."""
    failures = []
    locked = lock(_build(), now="2026-09-10T00:00:00")
    if not locked["locked_at"]:
        failures.append("lock() did not stamp locked_at")

    attempts = [
        (lambda: locked.__setitem__("symbol", "BBCA"), "top-level key"),
        (lambda: locked["facts"].__setitem__(0, {}), "a fact by position"),
        (lambda: locked["facts"][0].__setitem__("raw_value", 1), "a fact's value"),
        (lambda: locked["comparator"].__setitem__("mode", "yoy"), "the comparator"),
        (lambda: locked.append({}), "appending a fact"),
    ]
    for attempt, why in attempts:
        try:
            attempt()
        except FactSetLocked:
            continue
        failures.append(f"a locked FactSet was mutated: {why}")

    # Reading still works, and the copy that comes back out is a copy.
    if locked["symbol"] != "ADRO" or len(locked["facts"]) != 2 * len(UNITS):
        failures.append("a locked FactSet stopped being readable")
    mutable = unlock_copy(locked)
    mutable["symbol"] = "BBCA"
    if locked["symbol"] != "ADRO":
        failures.append("unlock_copy() handed back a live reference, not a copy")

    # An invalid FactSet may not be locked at all (PRD §15).
    try:
        lock(_build(rows=_rows(revenue=None)))
    except FactSetInvalid:
        pass
    else:
        failures.append("an unvalidated FactSet was locked")
    return failures, len(attempts) + 4


def check_restate():
    """A restatement is version 2 and names exactly what moved."""
    failures = []
    original = lock(_build(), now="2026-09-10T00:00:00")
    revenue_before = facts_for(unlock_copy(original), "target", "revenue")[0]["fact_id"]

    new, changed = restate(original, _rows(revenue=9_000_000_000_000),
                           as_of="2026-09-20", now="2026-09-20T00:00:00")
    if new["version"] != 2:
        failures.append(f"restatement produced version {new['version']}")
    if new["previous_version"] != 1 or not new.get("restates"):
        failures.append("the restatement does not point back at what it restates")
    if changed != [revenue_before]:
        failures.append(f"changed ids {changed}, expected only the revenue fact")
    if original["version"] != 1:
        failures.append("restating overwrote version 1 — the whole point of ER-FR-07")
    if new["as_of"] != "2026-09-20":
        failures.append("the restatement kept the old as_of")

    # An identical restatement changes nothing, and must say so rather than churning.
    same, unchanged = restate(original, _rows(), now="2026-09-20T00:00:00")
    if unchanged:
        failures.append(f"an identical restatement reported {len(unchanged)} changes")
    if same["source_hash"] != unlock_copy(original)["source_hash"]:
        failures.append("an identical restatement moved source_hash")
    return failures, 7


def main():
    results = [("determinism", *check_determinism()),
               ("provenance", *check_provenance()),
               ("validation reasons", *check_validate()),
               ("immutability", *check_lock()),
               ("restatement", *check_restate())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nfacts are frozen, identified by content, and restated rather than overwritten"
          if not failed else f"\n{failed} FactSet failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
