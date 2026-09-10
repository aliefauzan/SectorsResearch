#!/usr/bin/env python3
"""Task 16 — the PELAJARI step: what the agent does when it is wrong.

    python3 app/agent/lessons.py --dry-run     # prints each lesson, writes nothing
    python3 app/agent/lessons.py               # appends the new lessons
    python3 app/agent/lessons.py --context     # what the next screen would be handed

The judge's question is *"apa yang dilakukan agen ketika ia salah?"*, and the only
answer that survives contact with the repository is a file. This module is the
file: every outcome task 15 settles is turned into one structured row in
`state/lessons.jsonl`, and the rows from the last thirty days are handed back to
the next screen through `context()`. That last half is what makes this a loop
rather than an archive — a lesson nobody reads is a diary entry.

## Why the row is structured and not prose

The task is explicit: *"Jangan menulis lesson berupa teks bebas dari LLM tanpa
struktur."* The reason is downstream. Task 17 may move a bar only after twenty
resolved warnings agree on one axis, and it may move it only within that axis'
own floor and ceiling. Both of those are counts over `axis_implicated`, per
`subsector`. A paragraph cannot be counted, and an LLM asked for a paragraph will
happily produce a fluent one about an axis that never fired.

So the six fields of §4 are computed from the two rows that already exist — the
warning and its outcome — and nothing here invents anything that is not in them:

    conditions        every axis, its value, its bar, and whether it fired
    expected          the prediction the warning actually carried
    actual            what the label source and the price series recorded
    hypothesis        one sentence, naming the implicated axis and its margin
    axis_implicated   which bar is the most likely to be the wrong one
    subsector         because the bar for a mining stock is not the bar for a bank

Two extra keys ride along — `outcome` and `margin` — because `ledger.validate()`
allows unknown keys and task 17's aggregate would otherwise have to re-join every
lesson back to `outcomes.jsonl` to learn whether it describes a hit or a miss.

## Which outcomes teach

`true_positive` and `false_positive`. Step 2 of the task is emphatic that the
right answers teach too: a warning that fired at 0.61 concentration and was
followed by a suspension is evidence *for* that bar, and an evolution loop that
only ever sees its own failures will walk the bars in one direction forever.

The other two outcomes are deliberately not learned from, and the reasons differ:

  * `still_open` is a prediction in flight. It is written every tick a warning is
    still open, so learning from it would append a lesson per day per warning, and
    every one of them would have to guess at an `actual` that has not happened.
  * `expired` means the label source could not see the window — a shallow or stale
    `/v2/suspensions/` read, not a fact about the market. Any hypothesis drawn
    from it would blame an axis for a blind spot in the corpus, and because task
    17 counts lessons per axis, that mistake would not merely be wrong, it would
    move a real bar.

Both are counted in `skipped()` rather than silently dropped, so the tick can say
how many warnings it declined to learn from and why.

## One lesson per warning, forever

A warning has exactly one terminal outcome, so it gets exactly one lesson, keyed
by `warning_id`. Re-running the tick appends nothing — the same property task 15
gives `outcomes.jsonl`, for the same reason: the scheduler retries, and a file
that grows on retry is a record of cron, not of learning.

Zero credits. Warnings, outcomes and lessons are local files; the subsector map is
built from payloads already in `research/harness/recorded/`. No client is imported
here, so nothing in this module can open a socket.
"""
import argparse
import os
import re
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import labels, ledger, profile as profile_mod, universe  # noqa: E402
from app.cache import Cache  # noqa: E402

# The two outcomes a lesson may be written from. See the module docstring for why
# `still_open` and `expired` are not among them.
LEARNABLE = ("true_positive", "false_positive")

# Step 3: the window of lessons handed to the next screen.
DEFAULT_WINDOW_DAYS = 30

# Short Indonesian names for the axes, for the two prose fields. The long form
# lives in `profile.MEASURES` and is not repeated here.
AXIS_LABELS = {
    "concentration": "konsentrasi",
    "volume_anomaly": "volume",
    "momentum": "momentum",
    "catalyst": "katalis",
    "history": "riwayat suspensi",
}

# Which axes read their bar downwards. Derived from `profile.DIRECTIONS` rather
# than restated, so an axis that changes direction there changes it here too — a
# margin computed against the wrong side of the bar would implicate the wrong axis.
FIRES_BELOW = frozenset(
    axis for axis, text in profile_mod.DIRECTIONS.items()
    if text.startswith("di bawah"))

# What a symbol's subsector is called when no paid-for payload names it. A string,
# never an empty one: an empty field reads as a bug, this reads as an answer.
SUBSECTOR_UNKNOWN = "tidak diketahui"

SUBSECTOR_KEYS = ("sub_sector", "subsector")


# --- subsector, from payloads already paid for ------------------------------
def subsector_key(value):
    """The bucket a subsector name belongs to, whatever the payload called it.

    The API spells this field three ways in payloads already on disk:
    `/v2/company/report/?sections=overview` returns `"Oil, Gas & Coal"`,
    `/v2/filings/` returns the slug `"oil-gas-coal"`, and at least one row returns
    a bare lowercase `"banks"`. All three describe one subsector, and if they land
    in three buckets then `aggregate()` reports three subsectors with a third of
    the evidence each — which is exactly the count task 17's guards read.

    So the key is punctuation-free and case-free: `"Oil, Gas & Coal"` and
    `"oil-gas-coal"` both become `oil-gas-coal`. The key is internal; what the
    lesson carries is the display form chosen in `subsector_map`.
    """
    text = str(value or "").lower()
    words = [w for w in re.split(r"[^a-z0-9]+", text) if w]
    return "-".join(words)


def _display_rank(value):
    """Sort key that prefers the richest spelling of a subsector name.

    Mixed case beats both `"banks"` and `"BANKS"`; among equals the longer string
    wins, because it is the one that kept its punctuation — `"Oil, Gas & Coal"`
    over `"Oil Gas Coal"`. The final term is the value itself, so two candidates
    can never tie and the map cannot change between runs.
    """
    return (value == value.lower(), value == value.upper(), -len(value), value)


def _titled(key):
    """`"oil-gas-coal"` -> `"Oil Gas Coal"`, for a bucket only ever seen as a slug.

    A lesson is read on screen, so `holding-investment-companies` is not an answer
    to give a viewer. The punctuation the slug threw away — the comma in *Oil, Gas
    & Coal* — cannot be recovered here; it comes back on its own as soon as one
    payload spells the subsector out, because that spelling then wins the bucket.
    """
    return " ".join(word.capitalize() for word in key.split("-") if word)


def _display(key, spelling):
    """The name a lesson carries: the spelled-out form when one was seen, else titled."""
    if spelling and spelling != spelling.lower():
        return spelling
    return _titled(key)


_SUBSECTORS = None


def subsector_map(cache=None, reload=False):
    """`{symbol: subsector}` built by walking the settled recordings.

    The nearest enclosing `symbol` travels down the recursion, which is what makes
    the company-report shape work: the ticker sits at the top of the document and
    `sub_sector` sits inside `overview`, one level down and with no ticker of its
    own. Rows that carry both keys side by side — filings, news — are handled by
    the same walk without a special case.

    Names are collected under `subsector_key` and only then given a display form,
    which is what keeps the three spellings of one subsector in one bucket. When a
    symbol is filed under two different keys the smaller key wins: an arbitrary
    rule, but a *stable* one, and stability is what matters — a subsector that
    changed between runs would move lessons between the buckets task 17 counts.

    Only settled 2xx entries are read. A billed 404 proves the lookup ran, not that
    the identifier means anything, and folding its path segments in would invent
    tickers.
    """
    global _SUBSECTORS
    if cache is None and _SUBSECTORS is not None and not reload:
        return _SUBSECTORS

    source = cache if cache is not None else Cache()
    keys = {}       # symbol -> subsector key
    spellings = {}  # subsector key -> the best spelling seen for it

    def walk(node, symbol):
        if isinstance(node, dict):
            here = symbol
            for field in universe.SYMBOL_KEYS:
                value = node.get(field)
                if isinstance(value, str):
                    ticker = universe.normalize(value)
                    if universe.IDX_SYMBOL.match(ticker):
                        here = ticker
                        break
            for field in SUBSECTOR_KEYS:
                raw = node.get(field)
                if not isinstance(raw, str):
                    continue
                key = subsector_key(raw)
                if not key:
                    continue
                best = spellings.get(key)
                if best is None or _display_rank(raw.strip()) < _display_rank(best):
                    spellings[key] = raw.strip()
                if here and (here not in keys or key < keys[here]):
                    keys[here] = key
            for value in node.values():
                walk(value, here)
        elif isinstance(node, list):
            for value in node:
                walk(value, symbol)

    for entry in source.manifest().values():
        path = entry.get("path") or ""
        hit = source.get(path, entry.get("params"), entry.get("method", "GET"))
        if hit is None or not hit.found:
            continue
        walk(hit.payload, "")

    found = {symbol: _display(key, spellings.get(key))
             for symbol, key in keys.items()}
    if cache is None:
        _SUBSECTORS = found
    return found


def subsector(symbol, cache=None, table=None):
    """The subsector of one symbol, or `"tidak diketahui"`. Never a network call."""
    table = subsector_map(cache=cache) if table is None else table
    return table.get(universe.normalize(symbol), SUBSECTOR_UNKNOWN)


# --- reading one warning's axes ---------------------------------------------
def _axis_state(block):
    """The three-valued state of one axis block, tolerating an older row.

    `ledger.warning_row` writes `state`, but `warnings.jsonl` is append-only and
    rows written before it did are still valid against the schema. `fired` is the
    field the schema guarantees, so the state is derived from it when absent.
    """
    state = block.get("state")
    if state in (profile_mod.LIT, profile_mod.UNLIT, profile_mod.UNKNOWN):
        return state
    fired = block.get("fired")
    if fired is None:
        return profile_mod.UNKNOWN
    return profile_mod.LIT if fired else profile_mod.UNLIT


def _number(value):
    """A float, or None. Booleans are values, not numbers, and never a margin."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def margin(axis, block):
    """How far past its bar an axis read, signed so positive always means "past it".

    Catalyst reads downwards — a *low* share of fundamental coverage is the notable
    reading — so its margin is `threshold - value` while the other three are
    `value - threshold`. Without this the axis that cleared its bar by the most
    would look like the one that missed it by the most.
    """
    value = _number(block.get("value"))
    bar = _number(block.get("threshold"))
    if value is None or bar is None:
        return None
    return (bar - value) if axis in FIRES_BELOW else (value - bar)


def _relative(axis, block):
    """`margin` scaled by the bar, so axes on different units can be compared.

    Concentration is a share and volume anomaly is a multiple; 0.02 past the bar
    means something very different in each. Dividing by the bar makes "barely
    cleared" mean the same thing on both. A bar of zero has no scale to divide by,
    so the raw margin is used and the reader is not told a fraction that is not one.
    """
    raw = margin(axis, block)
    if raw is None:
        return None
    bar = _number(block.get("threshold"))
    if not bar:
        return raw
    return raw / abs(bar)


def _axis_order(warning):
    """Axes in reading order, counted ones first, then anything else on the row."""
    known = list(profile_mod.AXES) + list(profile_mod.SUPPORTING_AXES)
    axes = warning.get("axes") or {}
    return [a for a in known if a in axes] + [a for a in axes if a not in known]


def _format(value):
    """A number the way the lesson should read it: no trailing zeros, no `1e-05`."""
    number = _number(value)
    if number is None:
        if isinstance(value, bool):
            return "ya" if value else "tidak"
        return "tidak diukur"
    if number == int(number) and abs(number) < 1e15:
        return str(int(number))
    return f"{number:.4f}".rstrip("0").rstrip(".")


def implicated_axis(warning, outcome):
    """The axis whose bar this outcome says the most about, or None.

    The choice differs by outcome, and the asymmetry is the point:

      * a **false positive** implicates the axis that cleared its bar by the *least*
        — the weakest link in the warning, and the one whose bar is most plausibly
        too low;
      * a **true positive** implicates the axis that cleared it by the *most* — the
        witness that carried the call, and the bar most worth keeping where it is.

    Only axes that actually fired are eligible, because an axis that stayed dark
    did not contribute to the warning and cannot be blamed or credited for it. If
    none fired — possible for a hand-written row, not for one this system emits —
    the measured axis nearest its bar is named instead, and if nothing was measured
    the lesson carries `None` and says so in its hypothesis.
    """
    axes = warning.get("axes") or {}
    scored = []
    for axis in _axis_order(warning):
        block = axes.get(axis) or {}
        relative = _relative(axis, block)
        if relative is None:
            continue
        scored.append((axis, block.get("fired") is True, relative))
    if not scored:
        return None

    fired = [row for row in scored if row[1]]
    if not fired:
        # Nothing fired, so nothing can be blamed for the warning. The axis nearest
        # its bar — the *largest* margin, the least negative — is named so the
        # lesson still points somewhere, and `hypothesis_text` says plainly that it
        # did not fire. Ties keep reading order, so the choice is reproducible.
        return max(scored, key=lambda row: row[2])[0]
    if outcome == "true_positive":
        return max(fired, key=lambda row: row[2])[0]
    return min(fired, key=lambda row: row[2])[0]


# --- the six fields ---------------------------------------------------------
def conditions_text(warning):
    """Every axis as it read when the warning was written. §4's `conditions`."""
    axes = warning.get("axes") or {}
    parts = []
    for axis in _axis_order(warning):
        block = axes.get(axis) or {}
        label = AXIS_LABELS.get(axis, axis)
        state = _axis_state(block)
        if state == profile_mod.UNKNOWN:
            parts.append(f"{label} tidak terukur")
            continue
        bar = block.get("threshold")
        bar_text = "" if bar is None else f", ambang {_format(bar)}"
        parts.append(f"{label} {_format(block.get('value'))}{bar_text}, {state}")
    fired = warning.get("axes_fired")
    total = warning.get("axes_total")
    head = f"{fired} dari {total} sumbu menyala" if total else "sumbu"
    body = "; ".join(parts) if parts else "tidak ada sumbu tercatat"
    return f"{head} pada {warning.get('date')} — {body}"


def expected_text(warning):
    """What the warning said would happen. Read off the row, never re-derived."""
    prediction = warning.get("prediction") or ""
    when = warning.get("date")
    if prediction == ledger.PREDICTION:
        return (f"suspensi cooling-down dalam {ledger.PREDICTION_HORIZON_SESSIONS} "
                f"sesi bursa setelah {when}")
    return f"{prediction} setelah {when}" if prediction else f"tidak dinyatakan ({when})"


def _price_text(price):
    """The price half of `actual`, or an empty string when nothing was recorded."""
    if not price:
        return ""
    bits = []
    if "change_pct" in price:
        # The direction is said in words, not left to a minus sign a viewer has to
        # spot. Descriptive: what the close did, not what it means.
        change = _number(price["change_pct"]) or 0.0
        moved = "naik" if change > 0 else ("turun" if change < 0 else "bergerak")
        bits.append(f"harga {moved} {_format(abs(change))}% dari {price.get('from')} "
                    f"ke {price.get('through')}")
    if price.get("sessions_without_trade"):
        bits.append(f"{price['sessions_without_trade']} sesi tanpa transaksi")
    return "; ".join(bits)


def actual_text(outcome):
    """What the label source recorded. §4's `actual`, and never a guess.

    A miss is stated together with how far the search actually reached: *"tidak ada
    suspensi sampai X"* is a finding, *"tidak ada suspensi"* is an assertion.
    """
    evidence = outcome.get("evidence") or {}
    kind = outcome.get("outcome")
    price = _price_text(evidence.get("price"))

    if kind == "true_positive":
        text = (f"suspensi {evidence.get('reason_class') or 'tanpa kelas'} pada "
                f"{evidence.get('suspension_date')}, "
                f"{outcome.get('days_elapsed')} hari setelah peringatan")
        if evidence.get("pdf_url"):
            text += f" ({evidence['pdf_url']})"
    else:
        window = evidence.get("window") or {}
        through = evidence.get("checked_through") or window.get("last_session")
        text = f"tidak ada suspensi cooling-down sampai {through}"
        others = evidence.get("other_suspensions") or []
        if others:
            text += (f"; ada {len(others)} suspensi berkelas lain "
                     f"({others[0].get('reason_class')})")
    if price:
        text += f"; {price}"
    return text


def hypothesis_text(warning, outcome, axis, subsector_name):
    """One sentence naming the bar most likely to be wrong, and by how much.

    It is a hypothesis, not a finding, and the wording says so. Task 17 does not
    read this string — it counts `axis_implicated` — so nothing downstream depends
    on the prose. It exists because the video shows the lesson on screen, and a row
    of six machine fields does not explain itself to a viewer.
    """
    kind = outcome.get("outcome")
    if axis is None:
        return ("tidak ada sumbu terukur yang bisa dikaitkan dengan hasil ini; "
                "dugaan diarahkan ke kombinasi sumbu, bukan ke satu ambang")

    block = (warning.get("axes") or {}).get(axis) or {}
    label = AXIS_LABELS.get(axis, axis)
    side = "di bawah" if axis in FIRES_BELOW else "di atas"
    value = _format(block.get("value"))
    bar = _format(block.get("threshold"))
    gap = margin(axis, block)

    # The named axis did not clear its bar, so it is the nearest miss rather than
    # the weakest link. Saying "melewati ambangnya" here would be false, and the
    # bar it names is not the one to move — the axis-count rule is.
    if block.get("fired") is not True or gap is None or gap < 0:
        near = "tidak terukur" if gap is None else _format(abs(gap))
        return (f"{label} {value} tidak menyala terhadap ambang {bar} (selisih "
                f"{near}) dan itu sumbu terdekat dengan ambangnya pada peringatan "
                f"ini; dugaan diarahkan ke kombinasi sumbu, bukan ke satu ambang")

    if kind == "true_positive":
        return (f"{label} {value} berada {_format(gap)} {side} ambang {bar}; sumbu "
                f"ini yang paling jauh melewati ambangnya, jadi ambang {label} untuk "
                f"subsektor {subsector_name} tampak sudah pada tempatnya")
    return (f"{label} {value} melewati ambang {bar} hanya sejauh {_format(gap)} "
            f"{side}nya; sumbu ini yang paling tipis melewati ambang, jadi ambang "
            f"{label} untuk subsektor {subsector_name} mungkin masih terlalu longgar")


def lesson_for(warning, outcome, today=None, cache=None, table=None):
    """One warning plus its outcome, as one `lessons.jsonl` row.

    Pure: reads two dicts and a lookup table, writes nothing, opens no socket.
    """
    today = today or date.today()
    kind = outcome.get("outcome")
    axis = implicated_axis(warning, kind)
    name = subsector(warning.get("symbol"), cache=cache, table=table)
    block = (warning.get("axes") or {}).get(axis) if axis else None
    return {
        "warning_id": outcome.get("warning_id") or warning.get("id"),
        "written_on": today.isoformat(),
        "conditions": conditions_text(warning),
        "expected": expected_text(warning),
        "actual": actual_text(outcome),
        "hypothesis": hypothesis_text(warning, outcome, axis, name),
        "axis_implicated": axis,
        "subsector": name,
        # Not in §4's six. Carried because task 17 counts hits against misses per
        # axis, and `ledger.validate` allows a row to say more than the schema does.
        "outcome": kind,
        "margin": margin(axis, block) if block else None,
    }


# --- the tick step ----------------------------------------------------------
def _latest_terminal(outcomes):
    """`{warning_id: outcome}` for warnings that are closed, latest row winning."""
    closed = {}
    for row in outcomes:
        if row.get("outcome") in ledger.TERMINAL_OUTCOMES:
            closed[row["warning_id"]] = row
    return closed


def plan(today=None, warnings_path=None, outcomes_path=None, lessons_path=None,
         cache=None):
    """`(lessons, skipped)` — every lesson this tick would write. Writes nothing.

    `skipped` is a list of `(warning_id, reason)`, so a tick that learned from
    nothing can say whether that is because nothing closed or because everything
    that closed was `expired`.
    """
    today = today or date.today()
    warnings = {row["id"]: row for row in ledger.read_warnings(warnings_path)}
    outcomes = ledger.read_outcomes(outcomes_path)
    written = {row["warning_id"] for row in ledger.read_lessons(lessons_path)}
    table = subsector_map(cache=cache)

    rows, skipped = [], []
    for wid, outcome in _latest_terminal(outcomes).items():
        if wid in written:
            continue
        warning = warnings.get(wid)
        if warning is None:
            skipped.append((wid, "peringatannya tidak ada di warnings.jsonl"))
            continue
        if outcome["outcome"] not in LEARNABLE:
            skipped.append((wid, f"outcome {outcome['outcome']} tidak dipelajari — "
                                 f"sumber label tidak melihat jendelanya"))
            continue
        rows.append(lesson_for(warning, outcome, today=today, table=table))
    return rows, skipped


def run(today=None, warnings_path=None, outcomes_path=None, lessons_path=None,
        cache=None, dry_run=False):
    """Write the lessons this tick owes. `(lessons, skipped)`; idempotent on retry."""
    rows, skipped = plan(today=today, warnings_path=warnings_path,
                         outcomes_path=outcomes_path, lessons_path=lessons_path,
                         cache=cache)
    if not dry_run:
        for row in rows:
            ledger.append_lesson(row, path=lessons_path)
    return rows, skipped


# --- reading them back ------------------------------------------------------
def recent(days=DEFAULT_WINDOW_DAYS, today=None, path=None, lessons=None):
    """Lessons written in the last `days` days, oldest first.

    The window is inclusive at both ends and closed on the right: a lesson written
    exactly `days` ago is in, one written tomorrow is not. Dated rows only — a row
    whose `written_on` cannot be parsed is not silently treated as today's.
    """
    rows = lessons if lessons is not None else ledger.read_lessons(path)
    today = today or date.today()
    if days is None:
        return list(rows)
    since = today - timedelta(days=int(days))

    kept = []
    for row in rows:
        when = labels.parse_date(row.get("written_on"))
        if when is None or when < since or when > today:
            continue
        kept.append((when, row))
    kept.sort(key=lambda pair: pair[0])
    return [row for _when, row in kept]


def _bucket():
    return {"lessons": 0, "true_positive": 0, "false_positive": 0,
            "margins": {"true_positive": [], "false_positive": []}}


def _finish(bucket):
    out = {k: v for k, v in bucket.items() if k != "margins"}
    for kind, values in bucket["margins"].items():
        out[f"margin_mean_{kind}"] = (
            round(sum(values) / len(values), 6) if values else None)
    return out


def aggregate(lessons=None, days=DEFAULT_WINDOW_DAYS, today=None, path=None):
    """Counts per axis, per subsector, and per axis×subsector. Task 17's input.

    Task 17's first guard is *"N ≥ 20 peringatan selesai untuk sumbu itu"*, and
    `by_axis[axis]["lessons"]` is that N. The mean margin is carried beside it
    because a bar that produced six false positives says nothing about *where* to
    move; the average distance those six cleared it by does.

    The axis×subsector table is the third one because a mining stock's bar is not a
    bank's — that is the whole reason `subsector` is one of the six fields.
    """
    rows = lessons if lessons is not None else recent(days=days, today=today, path=path)
    by_axis, by_subsector, by_pair = {}, {}, {}
    for row in rows:
        kind = row.get("outcome")
        axis = row.get("axis_implicated")
        name = row.get("subsector") or SUBSECTOR_UNKNOWN
        gap = _number(row.get("margin"))
        for table, key in ((by_axis, axis), (by_subsector, name),
                           (by_pair, f"{axis}|{name}")):
            if key is None:
                continue
            bucket = table.setdefault(key, _bucket())
            bucket["lessons"] += 1
            if kind in bucket:
                bucket[kind] += 1
            if gap is not None and kind in bucket["margins"]:
                bucket["margins"][kind].append(gap)
    return {
        "lessons": len(rows),
        "by_axis": {k: _finish(v) for k, v in sorted(by_axis.items())},
        "by_subsector": {k: _finish(v) for k, v in sorted(by_subsector.items())},
        "by_axis_subsector": {k: _finish(v) for k, v in sorted(by_pair.items())},
    }


def context(days=DEFAULT_WINDOW_DAYS, today=None, path=None, lessons=None):
    """What the next screen is handed — step 3, the half that closes the loop.

    A screen that reads this knows, before it scores anything, which axis has been
    implicated most often lately and in which subsector. The rows are passed whole
    rather than summarised into a number: the aggregate says *how often*, and the
    individual `conditions`/`actual` pairs say *what it looked like*, which is what
    a reader — or a model given this as context — needs to recognise the pattern
    again.

    This function is the injection point and nothing calls it yet; the screen it
    feeds is a later task. It is defined here so that when that task arrives the
    contract is already fixed and already tested.
    """
    today = today or date.today()
    rows = recent(days=days, today=today, path=path, lessons=lessons)
    return {
        "window_days": days,
        "since": (today - timedelta(days=int(days))).isoformat() if days else None,
        "through": today.isoformat(),
        "lessons": rows,
        "aggregate": aggregate(lessons=rows),
    }


# --- CLI --------------------------------------------------------------------
def render(rows, skipped, dry_run):
    """The tick's own account of what it learned. Descriptive, no verdicts."""
    out = []
    verb = "akan ditulis" if dry_run else "ditulis"
    out.append(f"{len(rows)} pelajaran {verb}.")
    for row in rows:
        out.append(f"  {row['warning_id']} [{row['outcome']}] "
                   f"sumbu={row['axis_implicated']} subsektor={row['subsector']}")
        out.append(f"    kondisi : {row['conditions']}")
        out.append(f"    harapan : {row['expected']}")
        out.append(f"    kenyataan: {row['actual']}")
        out.append(f"    dugaan  : {row['hypothesis']}")
    for wid, reason in skipped:
        out.append(f"  dilewati {wid}: {reason}")
    return "\n".join(out)


def render_context(block):
    """The 30-day window as text, for the tick log and for the video."""
    out = [f"Pelajaran {block['since']} … {block['through']}: "
           f"{len(block['lessons'])} baris."]
    for axis, counts in block["aggregate"]["by_axis"].items():
        out.append(f"  {axis}: {counts['lessons']} pelajaran "
                   f"({counts['true_positive']} tepat, "
                   f"{counts['false_positive']} meleset)")
    for name, counts in block["aggregate"]["by_subsector"].items():
        out.append(f"  subsektor {name}: {counts['lessons']} pelajaran")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Tulis satu pelajaran terstruktur untuk tiap outcome baru.")
    parser.add_argument("--dry-run", action="store_true",
                        help="cetak pelajarannya, jangan tulis apa pun")
    parser.add_argument("--context", action="store_true",
                        help="cetak jendela pelajaran yang disuntikkan ke screen "
                             "berikutnya, jangan tulis apa pun")
    parser.add_argument("--days", type=int, default=DEFAULT_WINDOW_DAYS,
                        help=f"lebar jendela --context (default {DEFAULT_WINDOW_DAYS})")
    args = parser.parse_args(argv)

    if args.context:
        print(render_context(context(days=args.days)))
        return 0

    rows, skipped = run(dry_run=args.dry_run)
    print(render(rows, skipped, args.dry_run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
